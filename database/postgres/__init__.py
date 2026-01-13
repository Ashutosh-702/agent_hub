"""PostgreSQL database module for Agent Hub."""

from database.postgres.models import (
    Base,
    User,
    UserToken,
    Campaign,
    Company,
    Contact,
    CampaignCompanyRun,
    CampaignContactRun,
    Meeting,
    InboxLead,
    InboxEvent,
    InboxNote,
)
from database.postgres.base_dao import BasePostgresDao, generate_objectid, normalize_document
from database.postgres.engine import (
    PostgresEngine,
    get_postgres_engine,
    init_postgres,
    close_postgres,
)

__all__ = [
    # Models
    "Base",
    "User",
    "UserToken",
    "Campaign",
    "Company",
    "Contact",
    "CampaignCompanyRun",
    "CampaignContactRun",
    "Meeting",
    "InboxLead",
    "InboxEvent",
    "InboxNote",
    # Base DAO
    "BasePostgresDao",
    "generate_objectid",
    "normalize_document",
    # Engine
    "PostgresEngine",
    "get_postgres_engine",
    "init_postgres",
    "close_postgres",
]

