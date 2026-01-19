"""Tasks API Routes."""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import ORJSONResponse

from config.logging import logger
from ai_agents.tasks.constants import TaskStatus, EntityType
from ai_agents.tasks.schemas import (
    CreateTaskRequest, UpdateTaskRequest, LemlistEventRequest,
    ListTasksParams, ListTasksResponse, ListActivityResponse,
    TaskResponse, TaskDetailResponse, TaskLinkResponse,
    TaskActivityResponse, PaginatedNext, EntityBrief, UserBrief,
)
from ai_agents.tasks.service import get_task_service

# For user search
from database.factory import get_users_dao
from config.loaded_config import loaded_config


router = APIRouter(prefix="/tasks", tags=["Tasks"])


# =============================================================================
# Task CRUD Endpoints
# =============================================================================

@router.post("", response_model=TaskResponse)
async def create_task(request: CreateTaskRequest):
    """Create a new task.
    
    Creates a task linked to a contact, company, or deal.
    If the primary entity is a contact or deal with a company_id,
    the task will also be linked to that company.
    """
    try:
        service = get_task_service()
        
        # TODO: Get user ID from auth context
        created_by_user_id = None
        
        task = await service.create_task(
            request=request,
            created_by_user_id=created_by_user_id,
            source="ui",
        )
        
        return _task_to_response(task)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=ListTasksResponse)
async def list_tasks(
    statuses: Optional[str] = Query(None, description="Comma-separated statuses"),
    types: Optional[str] = Query(None, description="Comma-separated task types"),
    assigned_to_user_id: Optional[str] = Query(None),
    overdue: Optional[bool] = Query(None),
    entity_type: Optional[EntityType] = Query(None),
    entity_id: Optional[str] = Query(None),
    sl_no_lt: Optional[int] = Query(None, description="Pagination cursor"),
    limit: int = Query(50, ge=1, le=100),
):
    """List tasks with filters and keyset pagination.
    
    Use entity_type + entity_id to filter tasks linked to a specific entity.
    Returns tasks ordered by sl_no DESC (most recent first).
    """
    try:
        service = get_task_service()
        
        # Parse comma-separated values
        status_list = None
        if statuses:
            status_list = [TaskStatus(s.strip()) for s in statuses.split(",")]
        
        type_list = None
        if types:
            type_list = [t.strip() for t in types.split(",")]
        
        params = ListTasksParams(
            statuses=status_list,
            types=type_list,
            assigned_to_user_id=assigned_to_user_id,
            overdue=overdue,
            entity_type=entity_type,
            entity_id=entity_id,
            sl_no_lt=sl_no_lt,
            limit=limit,
        )
        
        tasks, next_sl_no = await service.list_tasks(params)
        
        return ListTasksResponse(
            items=[_task_to_response(t) for t in tasks],
            next=PaginatedNext(sl_no_lt=next_sl_no),
        )
        
    except Exception as e:
        logger.exception(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: str):
    """Get a task by ID with its links."""
    try:
        service = get_task_service()
        task = await service.get_task(task_id)
        
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        links = task.pop("links", [])
        
        return TaskDetailResponse(
            task=_task_to_response(task),
            links=[
                TaskLinkResponse(
                    entity_type=EntityType(link["entity_type"]),
                    entity_id=link["entity_id"],
                    entity_name=link.get("entity_name"),
                    link_reason=link["link_reason"],
                )
                for link in links
            ],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, request: UpdateTaskRequest):
    """Update a task.
    
    Updates status, priority, due_at, snoozed_until, assigned_to, title, or description.
    All changes are logged in the task activity.
    """
    try:
        service = get_task_service()
        
        # TODO: Get user ID from auth context
        actor_user_id = None
        
        task = await service.update_task(
            task_id=task_id,
            request=request,
            actor_user_id=actor_user_id,
        )
        
        return _task_to_response(task)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/activity", response_model=ListActivityResponse)
async def get_task_activity(
    task_id: str,
    sl_no_lt: Optional[int] = Query(None, description="Pagination cursor"),
    limit: int = Query(50, ge=1, le=100),
):
    """Get activity log for a task with keyset pagination."""
    try:
        service = get_task_service()
        
        activities, next_sl_no = await service.list_activity(
            task_id=task_id,
            sl_no_lt=sl_no_lt,
            limit=limit,
        )
        
        return ListActivityResponse(
            items=[_activity_to_response(a) for a in activities],
            next=PaginatedNext(sl_no_lt=next_sl_no),
        )
        
    except Exception as e:
        logger.exception(f"Error getting task activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Lemlist Integration
# =============================================================================

@router.post("/from-lemlist-event")
async def create_task_from_lemlist_event(event: LemlistEventRequest):
    """Create a call task from Lemlist first email open event.
    
    Flow:
    1. Looks up contact by email (required)
    2. Returns error if contact not found
    3. Creates task with rich context from Lemlist payload
    
    Idempotent - will return existing task if one already exists for
    the same email + campaign_id combination.
    
    Required fields:
    - email: Contact email address
    
    Optional fields:
    - firstName, lastName: For task title
    - companyName: For task title
    - sender: For task description
    - campaignId: For idempotency
    """
    try:
        # Store raw payload for context_json
        try:
            raw_payload = event.model_dump(exclude_none=True, exclude={"raw_payload"})
        except AttributeError:
            # Fallback for Pydantic v1
            raw_payload = event.dict(exclude_none=True)
        event.raw_payload = raw_payload
        
        service = get_task_service()
        task = await service.create_task_from_lemlist_event(event)
        
        if task is None:
            return ORJSONResponse({
                "success": False,
                "message": "Event not processed (not an email open event)"
            })
        
        return ORJSONResponse({
            "success": True,
            "task_id": task["_id"],
            "contact_id": task["primary_entity_id"],
            "message": "Task created or retrieved"
        })
        
    except ValueError as e:
        # Validation errors (e.g., contact not found)
        logger.warning(f"Validation error creating task from Lemlist event: {e}")
        return ORJSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=200)  # Return 200 to avoid Lemlist retrying
    except Exception as e:
        logger.exception(f"Error creating task from Lemlist event: {e}")
        return ORJSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=200)  # Return 200 to avoid Lemlist retrying


# =============================================================================
# User Search (for assignee type-ahead)
# =============================================================================

@router.get("/users/search")
async def search_users(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search users by name or email for assignee type-ahead."""
    try:
        users_dao = get_users_dao(loaded_config.connection_manager)
        
        # Search by email or name using Postgres-native search
        users = await users_dao.search_users(query=query, limit=limit)
        
        return ORJSONResponse({
            "items": [
                {
                    "id": u["_id"],
                    "email": u.get("email"),
                    "name": u.get("name"),
                }
                for u in users
            ]
        })
        
    except Exception as e:
        logger.exception(f"Error searching users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Entity Search (for entity picker type-ahead)
# =============================================================================

@router.get("/entities/search")
async def search_entities(
    entity_type: EntityType = Query(..., description="Entity type to search"),
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search entities by name/email for entity picker type-ahead."""
    try:
        connection_manager = loaded_config.connection_manager
        
        if entity_type == EntityType.CONTACT:
            from database.factory import get_contacts_dao
            dao = get_contacts_dao(connection_manager)
            entities = await dao.search_contacts(query=query, limit=limit)
            return ORJSONResponse({
                "items": [
                    {
                        "id": e["_id"],
                        "type": EntityType.CONTACT.value,
                        "name": f"{e.get('firstname', '')} {e.get('lastname', '')}".strip() or e.get("email", "Unknown"),
                        "email": e.get("email"),
                    }
                    for e in entities
                ]
            })
            
        elif entity_type == EntityType.COMPANY:
            from database.factory import get_companies_dao
            dao = get_companies_dao(connection_manager)
            entities = await dao.search_companies(query=query, limit=limit)
            return ORJSONResponse({
                "items": [
                    {
                        "id": e["_id"],
                        "type": EntityType.COMPANY.value,
                        "name": e.get("name", "Unknown"),
                    }
                    for e in entities
                ]
            })
            
        elif entity_type == EntityType.DEAL:
            from database.factory import get_deals_dao
            dao = get_deals_dao(connection_manager)
            entities = await dao.search_deals(query=query, limit=limit)
            return ORJSONResponse({
                "items": [
                    {
                        "id": e["_id"],
                        "type": EntityType.DEAL.value,
                        "name": e.get("name", "Unknown"),
                    }
                    for e in entities
                ]
            })
        
        return ORJSONResponse({"items": []})
        
    except Exception as e:
        logger.exception(f"Error searching entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Helper Functions
# =============================================================================

def _task_to_response(task: dict) -> TaskResponse:
    """Convert task dict to response model with enriched data."""
    # Extract enriched data if present
    assigned_to = None
    if task.get("assigned_to"):
        assigned_to = UserBrief(
            id=task["assigned_to"]["id"],
            name=task["assigned_to"].get("name"),
            email=task["assigned_to"].get("email"),
        )
    
    primary_entity = None
    if task.get("primary_entity"):
        primary_entity = EntityBrief(
            id=task["primary_entity"]["id"],
            type=task["primary_entity"]["type"],
            name=task["primary_entity"].get("name"),
            email=task["primary_entity"].get("email"),
        )
    
    return TaskResponse(
        id=task["_id"],
        sl_no=task.get("sl_no", 0),
        primary_entity_type=EntityType(task["primary_entity_type"]),
        primary_entity_id=task["primary_entity_id"],
        type=task["type"],
        status=TaskStatus(task["status"]),
        priority=task.get("priority", 3),
        due_at=task.get("due_at"),
        snoozed_until=task.get("snoozed_until"),
        completed_at=task.get("completed_at"),
        assigned_to_user_id=task.get("assigned_to_user_id"),
        owner_user_id=task.get("owner_user_id"),
        created_by_user_id=task.get("created_by_user_id"),
        title=task.get("title"),
        description=task.get("description"),
        source=task.get("source"),
        source_ref=task.get("source_ref"),
        context_json=task.get("context_json"),
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        effective_due_at=task.get("effective_due_at"),
        is_overdue=task.get("is_overdue", False),
        assigned_to=assigned_to,
        primary_entity=primary_entity,
    )


def _activity_to_response(activity: dict) -> TaskActivityResponse:
    """Convert activity dict to response model with enriched actor."""
    actor = None
    if activity.get("actor"):
        actor = UserBrief(
            id=activity["actor"]["id"],
            name=activity["actor"].get("name"),
            email=activity["actor"].get("email"),
        )
    
    return TaskActivityResponse(
        id=activity["_id"],
        sl_no=activity.get("sl_no", 0),
        task_id=activity["task_id"],
        at=activity["at"],
        actor_user_id=activity.get("actor_user_id"),
        event_type=activity["event_type"],
        diff_json=activity.get("diff_json", {}),
        actor=actor,
    )
