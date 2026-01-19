"""Constants for the Tasks module."""

from enum import Enum


class TaskStatus(str, Enum):
    """Task statuses."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task types."""
    CALL = "call"
    FOLLOWUP_EMAIL = "followup_email"
    REPLY_EMAIL = "reply_email"
    DATA_CLEAN = "data_clean"
    CUSTOM = "custom"


class EntityType(str, Enum):
    """Entity types that tasks can be linked to."""
    CONTACT = "contact"
    COMPANY = "company"
    DEAL = "deal"


class LinkReason(str, Enum):
    """Reasons for task-entity links."""
    PRIMARY = "primary"
    DERIVED_COMPANY = "derived_company"


class TaskEventType(str, Enum):
    """Task activity event types."""
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    SNOOZED = "snoozed"
    COMPLETED = "completed"
    REOPENED = "reopened"


# Default task priorities (1 = highest, 5 = lowest)
PRIORITY_HIGH = 1
PRIORITY_MEDIUM_HIGH = 2
PRIORITY_MEDIUM = 3
PRIORITY_MEDIUM_LOW = 4
PRIORITY_LOW = 5
