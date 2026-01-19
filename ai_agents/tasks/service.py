"""Tasks service - Business logic for task management."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple

from config.loaded_config import loaded_config
from config.logging import logger
from database.factory import (
    get_tasks_dao,
    get_task_type_policies_dao,
    get_task_activity_dao,
    get_task_links_dao,
    get_companies_dao,
    get_contacts_dao,
    get_deals_dao,
)
from database.postgres.base_dao import generate_objectid

from ai_agents.tasks.constants import (
    TaskStatus, TaskType, EntityType, LinkReason, TaskEventType,
    PRIORITY_MEDIUM, PRIORITY_HIGH
)
from ai_agents.tasks.schemas import (
    CreateTaskRequest, UpdateTaskRequest, LemlistEventRequest,
    ListTasksParams, TaskResponse, TaskActivityResponse,
    TaskLinkResponse, EntityBrief, PaginatedNext,
)


class TaskService:
    """Service for managing tasks."""

    def __init__(self):
        self.connection_manager = loaded_config.connection_manager

    def _get_tasks_dao(self):
        return get_tasks_dao(self.connection_manager)
    
    def _get_policies_dao(self):
        return get_task_type_policies_dao(self.connection_manager)
    
    def _get_activity_dao(self):
        return get_task_activity_dao(self.connection_manager)
    
    def _get_links_dao(self):
        return get_task_links_dao(self.connection_manager)
    
    def _get_contacts_dao(self):
        return get_contacts_dao(self.connection_manager)
    
    def _get_companies_dao(self):
        return get_companies_dao(self.connection_manager)
    
    def _get_deals_dao(self):
        return get_deals_dao(self.connection_manager)

    async def create_task(
        self,
        request: CreateTaskRequest,
        created_by_user_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        source: Optional[str] = None,
        source_ref: Optional[str] = None,
        context_json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new task.
        
        Args:
            request: Task creation request
            created_by_user_id: User who created the task
            idempotency_key: Optional idempotency key for deduplication
            source: Source of the task (ui, lemlist, etc.)
            source_ref: Reference ID from source
            context_json: Additional context data
            
        Returns:
            Created task dict
        """
        # Use a single session context for all operations
        async with self.connection_manager.pg_session_context() as session:
            # Get entity info and owner
            entity_info = await self._get_entity_info(
                request.primary_entity_type,
                request.primary_entity_id,
                session=session
            )
            
            if entity_info is None:
                raise ValueError(f"Entity not found: {request.primary_entity_type}:{request.primary_entity_id}")
            
            entity_owner_id = entity_info.get("owner_user_id")
            company_id = entity_info.get("company_id")
            
            # Get policy for task type
            policies_dao = get_task_type_policies_dao(self.connection_manager)
            policies_dao._session = session  # Use the same session
            policy = await policies_dao.get_policy(request.type)
            
            # Compute defaults
            priority = request.priority or (policy["default_priority"] if policy else PRIORITY_MEDIUM)
            
            # Handle due_at - convert to timezone-naive UTC if timezone-aware
            due_at = request.due_at
            if due_at is None and policy:
                due_at = datetime.utcnow() + timedelta(minutes=policy["default_sla_minutes"])
            elif due_at is not None:
                # Convert timezone-aware datetime to timezone-naive UTC
                if due_at.tzinfo is not None:
                    due_at = due_at.astimezone(timezone.utc).replace(tzinfo=None)
            
            # Assignee defaults to entity owner, then created_by
            assigned_to = request.assigned_to_user_id or entity_owner_id or created_by_user_id
            
            # Build task data - ensure all datetimes are timezone-naive UTC
            now = datetime.utcnow()
            task_data = {
                "id": generate_objectid(),
                "primary_entity_type": request.primary_entity_type.value,
                "primary_entity_id": request.primary_entity_id,
                "type": request.type,
                "status": TaskStatus.OPEN.value,
                "priority": priority,
                "due_at": due_at,
                "assigned_to_user_id": assigned_to,
                "owner_user_id": entity_owner_id,
                "created_by_user_id": created_by_user_id,
                "title": request.title,
                "description": request.description,
                "source": source or "ui",
                "source_ref": source_ref,
                "idempotency_key": idempotency_key,
                "context_json": context_json or {},
                "created_at": now,
                "updated_at": now,
            }
            
            # Create task (idempotent) - use same session
            tasks_dao = get_tasks_dao(self.connection_manager)
            tasks_dao._session = session
            if idempotency_key:
                task = await tasks_dao.create_task_idempotent(task_data)
            else:
                task_id = await tasks_dao.insert_one(task_data)
                task = await tasks_dao.find_one({"_id": task_id})
            
            # Create links - use same session
            links_dao = get_task_links_dao(self.connection_manager)
            links_dao._session = session
            
            # Primary link
            await links_dao.create_link_idempotent(
                task_id=task["_id"],
                entity_type=request.primary_entity_type.value,
                entity_id=request.primary_entity_id,
                link_reason=LinkReason.PRIMARY.value,
            )
            
            # Derived company link (for contact/deal tasks)
            if request.primary_entity_type != EntityType.COMPANY and company_id:
                await links_dao.create_link_idempotent(
                    task_id=task["_id"],
                    entity_type=EntityType.COMPANY.value,
                    entity_id=company_id,
                    link_reason=LinkReason.DERIVED_COMPANY.value,
                )
            
            # Create activity entry - use same session
            activity_dao = get_task_activity_dao(self.connection_manager)
            activity_dao._session = session
            await activity_dao.add_activity(
                task_id=task["_id"],
                event_type=TaskEventType.CREATED.value,
                diff_json={"after": task},
                actor_user_id=created_by_user_id,
            )
            
            logger.info(f"Created task", task_id=task["_id"], type=request.type)
            return task

    async def update_task(
        self,
        task_id: str,
        request: UpdateTaskRequest,
        actor_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a task.
        
        Args:
            task_id: Task ID
            request: Update request
            actor_user_id: User performing the update
            
        Returns:
            Updated task dict
        """
        tasks_dao = self._get_tasks_dao()
        existing = await tasks_dao.get_task_by_id(task_id)
        
        if existing is None:
            raise ValueError(f"Task not found: {task_id}")
        
        # Build updates
        updates = {}
        before = {}
        after = {}
        
        if request.status is not None and request.status.value != existing.get("status"):
            before["status"] = existing.get("status")
            after["status"] = request.status.value
            updates["status"] = request.status.value
            
            # Handle completion
            if request.status == TaskStatus.DONE:
                updates["completed_at"] = datetime.utcnow()
            elif existing.get("status") == TaskStatus.DONE.value:
                updates["completed_at"] = None
            
            # Validate snooze
            if request.status == TaskStatus.SNOOZED:
                if not request.snoozed_until:
                    raise ValueError("Snoozed status requires snoozed_until")
                # Convert to timezone-naive UTC for comparison
                snoozed_until_naive = request.snoozed_until
                if snoozed_until_naive.tzinfo is not None:
                    snoozed_until_naive = snoozed_until_naive.astimezone(timezone.utc).replace(tzinfo=None)
                now_naive = datetime.utcnow()
                if snoozed_until_naive <= now_naive:
                    raise ValueError("Snoozed status requires snoozed_until > now")
        
        if request.priority is not None and request.priority != existing.get("priority"):
            before["priority"] = existing.get("priority")
            after["priority"] = request.priority
            updates["priority"] = request.priority
        
        if request.due_at is not None:
            before["due_at"] = existing.get("due_at")
            # Convert to timezone-naive UTC if timezone-aware
            due_at_naive = request.due_at
            if due_at_naive.tzinfo is not None:
                due_at_naive = due_at_naive.astimezone(timezone.utc).replace(tzinfo=None)
            after["due_at"] = due_at_naive
            updates["due_at"] = due_at_naive
        
        if request.snoozed_until is not None:
            before["snoozed_until"] = existing.get("snoozed_until")
            # Convert to timezone-naive UTC if timezone-aware
            snoozed_until_naive = request.snoozed_until
            if snoozed_until_naive.tzinfo is not None:
                snoozed_until_naive = snoozed_until_naive.astimezone(timezone.utc).replace(tzinfo=None)
            after["snoozed_until"] = snoozed_until_naive
            updates["snoozed_until"] = snoozed_until_naive
        
        if request.assigned_to_user_id is not None and request.assigned_to_user_id != existing.get("assigned_to_user_id"):
            before["assigned_to_user_id"] = existing.get("assigned_to_user_id")
            after["assigned_to_user_id"] = request.assigned_to_user_id
            updates["assigned_to_user_id"] = request.assigned_to_user_id
        
        if request.title is not None:
            before["title"] = existing.get("title")
            after["title"] = request.title
            updates["title"] = request.title
        
        if request.description is not None:
            before["description"] = existing.get("description")
            after["description"] = request.description
            updates["description"] = request.description
        
        if not updates:
            return existing
        
        updates["updated_at"] = datetime.utcnow()
        
        # Apply updates
        await tasks_dao.update_task(task_id, updates)
        
        # Create activity entry
        activity_dao = self._get_activity_dao()
        await activity_dao.add_activity(
            task_id=task_id,
            event_type=TaskEventType.UPDATED.value,
            diff_json={"before": before, "after": after},
            actor_user_id=actor_user_id,
        )
        
        # Fetch updated task
        updated = await tasks_dao.get_task_by_id(task_id)
        
        logger.info(f"Updated task", task_id=task_id, changes=list(updates.keys()))
        return updated

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID with links and enriched names.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dict with links and enriched names or None
        """
        tasks_dao = self._get_tasks_dao()
        task = await tasks_dao.get_task_by_id(task_id)
        
        if task is None:
            return None
        
        # Get links
        links_dao = self._get_links_dao()
        links = await links_dao.get_links_for_task(task_id)
        
        # Enrich links with entity names
        enriched_links = await self._enrich_links(links)
        task["links"] = enriched_links
        
        # Enrich task with assignee name
        if task.get("assigned_to_user_id"):
            assignee = await self._get_user_brief(task["assigned_to_user_id"])
            if assignee:
                task["assigned_to"] = assignee
        
        # Enrich task with primary entity name
        primary_entity = await self._get_entity_brief(
            task["primary_entity_type"],
            task["primary_entity_id"]
        )
        if primary_entity:
            task["primary_entity"] = primary_entity
        
        return task

    async def list_tasks(
        self,
        params: ListTasksParams,
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """List tasks with filters and pagination.
        
        Args:
            params: List parameters
            
        Returns:
            Tuple of (tasks list, next sl_no_lt cursor)
        """
        tasks_dao = self._get_tasks_dao()
        
        # Convert status enums to strings
        status_values = [s.value for s in params.statuses] if params.statuses else None
        
        if params.entity_type and params.entity_id:
            # Entity-filtered query
            tasks = await tasks_dao.list_tasks_by_entity(
                entity_type=params.entity_type.value,
                entity_id=params.entity_id,
                statuses=status_values,
                assigned_to_user_id=params.assigned_to_user_id,
                types=params.types,
                sl_no_lt=params.sl_no_lt,
                limit=params.limit + 1,  # Fetch one extra to determine if there's a next page
            )
        else:
            # Inbox query
            tasks = await tasks_dao.list_tasks_inbox(
                statuses=status_values,
                assigned_to_user_id=params.assigned_to_user_id,
                types=params.types,
                overdue=params.overdue,
                sl_no_lt=params.sl_no_lt,
                limit=params.limit + 1,
            )
        
        # Determine next cursor
        next_sl_no = None
        if len(tasks) > params.limit:
            tasks = tasks[:params.limit]
            next_sl_no = tasks[-1]["sl_no"] if tasks else None
        
        # Enrich tasks with computed fields and names
        now = datetime.utcnow()
        for task in tasks:
            task["effective_due_at"] = self._compute_effective_due_at(task, now)
            task["is_overdue"] = self._is_overdue(task, now)
            
            # Enrich with assignee name
            if task.get("assigned_to_user_id"):
                assignee = await self._get_user_brief(task["assigned_to_user_id"])
                if assignee:
                    task["assigned_to"] = assignee
            
            # Enrich with primary entity name
            primary_entity = await self._get_entity_brief(
                task["primary_entity_type"],
                task["primary_entity_id"]
            )
            if primary_entity:
                task["primary_entity"] = primary_entity
        
        return tasks, next_sl_no

    async def list_activity(
        self,
        task_id: str,
        sl_no_lt: Optional[int] = None,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """List activity for a task with enriched actor names.
        
        Args:
            task_id: Task ID
            sl_no_lt: Pagination cursor
            limit: Max results
            
        Returns:
            Tuple of (activity list, next sl_no_lt cursor)
        """
        activity_dao = self._get_activity_dao()
        activities = await activity_dao.list_activity(
            task_id=task_id,
            sl_no_lt=sl_no_lt,
            limit=limit + 1,
        )
        
        next_sl_no = None
        if len(activities) > limit:
            activities = activities[:limit]
            next_sl_no = activities[-1]["sl_no"] if activities else None
        
        # Enrich activities with actor names
        for activity in activities:
            if activity.get("actor_user_id"):
                actor = await self._get_user_brief(activity["actor_user_id"])
                if actor:
                    activity["actor"] = actor
        
        return activities, next_sl_no

    async def create_task_from_lemlist_event(
        self,
        event: LemlistEventRequest,
    ) -> Optional[Dict[str, Any]]:
        """Create a call task from Lemlist first email open event.
        
        Flow:
        1. Look up contact by email (required)
        2. If contact not found, return error
        3. Create task with rich context from Lemlist payload
        
        Args:
            event: Lemlist event data (must include email)
            
        Returns:
            Created task or existing task (idempotent)
        """
        if event.type and event.type != "emailsOpened":
            logger.info(f"Ignoring non-open event", event_type=event.type)
            return None
        
        if not event.email:
            logger.warning("Lemlist event missing email")
            raise ValueError("Email is required to create task from Lemlist event")
        
        # Use a single session for all operations
        async with self.connection_manager.pg_session_context() as session:
            # Look up contact by email (case-insensitive)
            contacts_dao = get_contacts_dao(self.connection_manager)
            contacts_dao._session = session
            
            # Search for contact by email
            contacts = await contacts_dao.search_contacts(query=event.email, limit=1)
            
            if not contacts:
                raise ValueError(f"Contact not found for email: {event.email}. Please create contact first.")
            
            contact = contacts[0]
            contact_id = contact["_id"]
            
            # Build title: "Call: {firstName} {lastName} from {companyName}"
            first_name = event.first_name or contact.get("firstname", "")
            last_name = event.last_name or contact.get("lastname", "")
            contact_name = f"{first_name} {last_name}".strip() or event.email
            
            company_name = event.company_name or "Unknown Company"
            title = f"Call: {contact_name} from {company_name}"
            
            # Build description with sender info
            description_parts = ["Opened email from campaign."]
            if event.sender and event.sender.get("name"):
                description_parts.append(f"Sender: {event.sender.get('name')}")
            if event.campaign_id:
                description_parts.append(f"Campaign: {event.campaign_id}")
            description = " ".join(description_parts)
            
            # Build idempotency key using email + campaign (since contactId might not be in our system)
            campaign_part = event.campaign_id or "unknown"
            idempotency_key = f"lemlist:first_open_call:{event.email}:{campaign_part}"
            
            # Store full Lemlist payload in context_json
            # Use raw_payload if provided, otherwise serialize the event model
            lemlist_payload = event.raw_payload
            if not lemlist_payload:
                # Convert Pydantic model to dict
                try:
                    lemlist_payload = event.model_dump(exclude_none=True, exclude={"raw_payload"})
                except AttributeError:
                    # Fallback for Pydantic v1
                    lemlist_payload = event.dict(exclude_none=True)
            
            context_json = {
                "lemlist_payload": lemlist_payload,
                "trigger": {
                    "type": event.type or "emailsOpened",
                    "email": event.email,
                    "contact_id": contact_id,
                    "campaign_id": event.campaign_id,
                    "lead_id": event.lead_id,
                    "message_id": event.message_id,
                    "sender": event.sender,
                }
            }
            
            # Create task request with high priority (1 = top)
            request = CreateTaskRequest(
                primary_entity_type=EntityType.CONTACT,
                primary_entity_id=contact_id,
                type=TaskType.CALL.value,
                title=title,
                description=description,
                priority=PRIORITY_HIGH,  # Priority 1 (top)
            )
            
            source_ref = f"lemlist:email:{event.email},campaign:{event.campaign_id or 'none'}"
            
            try:
                task = await self.create_task(
                    request=request,
                    idempotency_key=idempotency_key,
                    source="lemlist",
                    source_ref=source_ref,
                    context_json=context_json,
                )
                
                logger.info(f"Created/retrieved Lemlist task", 
                           task_id=task["_id"], 
                           contact_id=contact_id,
                           email=event.email)
                return task
                
            except ValueError as e:
                logger.warning(f"Failed to create Lemlist task: {e}")
                raise

    async def _get_user_brief(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user brief (id, name, email) for enrichment.
        
        Args:
            user_id: User ID
            
        Returns:
            User brief dict or None
        """
        try:
            from database.factory import get_users_dao
            users_dao = get_users_dao(self.connection_manager)
            user = await users_dao.find_one({"_id": user_id})
            if user:
                return {
                    "id": user["_id"],
                    "name": user.get("name"),
                    "email": user.get("email"),
                }
        except Exception as e:
            logger.warning(f"Failed to fetch user {user_id}: {e}")
        return None
    
    async def _get_entity_brief(
        self,
        entity_type: str,
        entity_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get entity brief (id, type, name, email) for enrichment.
        
        Args:
            entity_type: Entity type string
            entity_id: Entity ID
            
        Returns:
            Entity brief dict or None
        """
        try:
            entity_type_enum = EntityType(entity_type)
            
            if entity_type_enum == EntityType.CONTACT:
                contacts_dao = self._get_contacts_dao()
                contact = await contacts_dao.get_contact(entity_id)
                if contact:
                    name = f"{contact.get('firstname', '')} {contact.get('lastname', '')}".strip()
                    return {
                        "id": contact["_id"],
                        "type": EntityType.CONTACT,
                        "name": name or contact.get("email", "Unknown"),
                        "email": contact.get("email"),
                    }
            
            elif entity_type_enum == EntityType.COMPANY:
                companies_dao = self._get_companies_dao()
                company = await companies_dao.find_one({"_id": entity_id})
                if company:
                    return {
                        "id": company["_id"],
                        "type": EntityType.COMPANY,
                        "name": company.get("name", "Unknown"),
                        "email": None,
                    }
            
            elif entity_type_enum == EntityType.DEAL:
                deals_dao = self._get_deals_dao()
                deal = await deals_dao.get_deal_by_id(entity_id)
                if deal:
                    return {
                        "id": deal["_id"],
                        "type": EntityType.DEAL,
                        "name": deal.get("name", "Unknown"),
                        "email": None,
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch entity {entity_type}:{entity_id}: {e}")
        return None
    
    async def _enrich_links(
        self,
        links: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Enrich task links with entity names.
        
        Args:
            links: List of link dicts
            
        Returns:
            List of enriched link dicts
        """
        enriched = []
        for link in links:
            entity_type = link.get("entity_type")
            entity_id = link.get("entity_id")
            
            entity_brief = await self._get_entity_brief(entity_type, entity_id)
            enriched_link = link.copy()
            if entity_brief:
                enriched_link["entity_name"] = entity_brief.get("name")
            else:
                enriched_link["entity_name"] = None
            enriched.append(enriched_link)
        
        return enriched

    async def _get_entity_info(
        self,
        entity_type: EntityType,
        entity_id: str,
        session=None,
    ) -> Optional[Dict[str, Any]]:
        """Get entity info including owner_user_id and company_id.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
            
        Returns:
            Entity info dict or None
        """
        if entity_type == EntityType.CONTACT:
            contacts_dao = self._get_contacts_dao()
            if session:
                contacts_dao._session = session
            contact = await contacts_dao.get_contact(entity_id)
            if contact:
                return {
                    "id": contact["_id"],
                    "type": EntityType.CONTACT.value,
                    "name": f"{contact.get('firstname', '')} {contact.get('lastname', '')}".strip(),
                    "email": contact.get("email"),
                    "owner_user_id": contact.get("owner_user_id"),
                    "company_id": contact.get("company_id"),
                }
            return None
            
        elif entity_type == EntityType.COMPANY:
            companies_dao = self._get_companies_dao()
            if session:
                companies_dao._session = session
            company = await companies_dao.find_one({"_id": entity_id})
            if company:
                return {
                    "id": company["_id"],
                    "type": EntityType.COMPANY.value,
                    "name": company.get("name"),
                    "owner_user_id": company.get("owner_user_id"),
                    "company_id": None,  # No parent company
                }
            return None
            
        elif entity_type == EntityType.DEAL:
            deals_dao = self._get_deals_dao()
            if session:
                deals_dao._session = session
            deal = await deals_dao.get_deal_by_id(entity_id)
            if deal:
                return {
                    "id": deal["_id"],
                    "type": EntityType.DEAL.value,
                    "name": deal.get("name"),
                    "owner_user_id": deal.get("owner_user_id"),
                    "company_id": deal.get("company_id"),
                }
            return None
        
        return None

    def _compute_effective_due_at(
        self,
        task: Dict[str, Any],
        now: datetime,
    ) -> Optional[datetime]:
        """Compute effective due date considering snooze.
        
        All datetimes are normalized to timezone-naive UTC for comparison.
        """
        # Ensure 'now' is timezone-naive
        if now.tzinfo is not None:
            now = now.astimezone(timezone.utc).replace(tzinfo=None)
        
        snoozed_until = task.get("snoozed_until")
        due_at = task.get("due_at")
        
        # Normalize snoozed_until to timezone-naive UTC
        if snoozed_until:
            if isinstance(snoozed_until, datetime):
                if snoozed_until.tzinfo is not None:
                    snoozed_until = snoozed_until.astimezone(timezone.utc).replace(tzinfo=None)
                if snoozed_until > now:
                    return snoozed_until
        
        # Normalize due_at to timezone-naive UTC
        if due_at:
            if isinstance(due_at, datetime):
                if due_at.tzinfo is not None:
                    due_at = due_at.astimezone(timezone.utc).replace(tzinfo=None)
        
        return due_at

    def _is_overdue(
        self,
        task: Dict[str, Any],
        now: datetime,
    ) -> bool:
        """Check if task is overdue.
        
        All datetimes are normalized to timezone-naive UTC for comparison.
        """
        status = task.get("status")
        if status not in [TaskStatus.OPEN.value, TaskStatus.IN_PROGRESS.value]:
            return False
        
        # Ensure 'now' is timezone-naive
        if now.tzinfo is not None:
            now = now.astimezone(timezone.utc).replace(tzinfo=None)
        
        effective_due = self._compute_effective_due_at(task, now)
        if effective_due is None:
            return False
        
        # effective_due is already normalized by _compute_effective_due_at
        return effective_due < now


# Singleton instance
_task_service: Optional[TaskService] = None


def get_task_service() -> TaskService:
    """Get or create task service instance."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service
