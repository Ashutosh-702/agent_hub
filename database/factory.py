"""DAO Factory for selecting between MongoDB and PostgreSQL implementations.

This factory uses feature flags to determine which database backend to use
for each collection, enabling gradual migration from MongoDB to PostgreSQL.
"""

from typing import Union

from config.loaded_config import Settings


def get_users_dao(connection_manager) -> Union["UsersDao", "PostgresUsersDao"]:
    """Get the appropriate Users DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        UsersDao (MongoDB) or PostgresUsersDao (PostgreSQL)
    """
    if Settings.use_postgres("users"):
        from database.postgres.collection_dao.users import PostgresUsersDao
        session = connection_manager.get_pg_session()
        dao = PostgresUsersDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.users import UsersDao
        return UsersDao(connection_manager.mongo_client)


def get_user_tokens_dao(connection_manager) -> Union["UserTokensDao", "PostgresUserTokensDao"]:
    """Get the appropriate UserTokens DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        UserTokensDao (MongoDB) or PostgresUserTokensDao (PostgreSQL)
    """
    if Settings.use_postgres("user_tokens"):
        from database.postgres.collection_dao.user_tokens import PostgresUserTokensDao
        session = connection_manager.get_pg_session()
        dao = PostgresUserTokensDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.user_tokens import UserTokensDao
        return UserTokensDao(connection_manager.mongo_client)


def get_campaigns_dao(connection_manager) -> Union["CampaignsDao", "PostgresCampaignsDao"]:
    """Get the appropriate Campaigns DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        CampaignsDao (MongoDB) or PostgresCampaignsDao (PostgreSQL)
    """
    if Settings.use_postgres("campaigns"):
        from database.postgres.collection_dao.campaigns import PostgresCampaignsDao
        session = connection_manager.get_pg_session()
        dao = PostgresCampaignsDao(session)
        # Pass session factory for connection pool management
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.campaigns import CampaignsDao
        return CampaignsDao(connection_manager.mongo_client)


def get_companies_dao(connection_manager) -> Union["CompaniesDao", "PostgresCompaniesDao"]:
    """Get the appropriate Companies DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        CompaniesDao (MongoDB) or PostgresCompaniesDao (PostgreSQL)
    """
    if Settings.use_postgres("companies"):
        from database.postgres.collection_dao.companies import PostgresCompaniesDao
        session = connection_manager.get_pg_session()
        dao = PostgresCompaniesDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.companies import CompaniesDao
        return CompaniesDao(connection_manager.mongo_client)


def get_contacts_dao(connection_manager) -> Union["ContactsDao", "PostgresContactsDao"]:
    """Get the appropriate Contacts DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        ContactsDao (MongoDB) or PostgresContactsDao (PostgreSQL)
    """
    if Settings.use_postgres("contacts"):
        from database.postgres.collection_dao.contacts import PostgresContactsDao
        session = connection_manager.get_pg_session()
        dao = PostgresContactsDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.contacts import ContactsDao
        return ContactsDao(connection_manager.mongo_client)


def get_campaign_company_runs_dao(connection_manager) -> Union["CampaignCompanyRunsDao", "PostgresCampaignCompanyRunsDao"]:
    """Get the appropriate CampaignCompanyRuns DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        CampaignCompanyRunsDao (MongoDB) or PostgresCampaignCompanyRunsDao (PostgreSQL)
    """
    if Settings.use_postgres("campaign_company_runs"):
        from database.postgres.collection_dao.campaign_company_runs import PostgresCampaignCompanyRunsDao
        session = connection_manager.get_pg_session()
        dao = PostgresCampaignCompanyRunsDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
        return CampaignCompanyRunsDao(connection_manager.mongo_client)


def get_campaign_contact_runs_dao(connection_manager) -> Union["CampaignContactRunsDao", "PostgresCampaignContactRunsDao"]:
    """Get the appropriate CampaignContactRuns DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        CampaignContactRunsDao (MongoDB) or PostgresCampaignContactRunsDao (PostgreSQL)
    """
    if Settings.use_postgres("campaign_contact_runs"):
        from database.postgres.collection_dao.campaign_contact_runs import PostgresCampaignContactRunsDao
        session = connection_manager.get_pg_session()
        dao = PostgresCampaignContactRunsDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.campaign_contact_runs import CampaignContactRunsDao
        return CampaignContactRunsDao(connection_manager.mongo_client)


def get_meetings_dao(connection_manager) -> Union["MeetingsDao", "PostgresMeetingsDao"]:
    """Get the appropriate Meetings DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        MeetingsDao (MongoDB) or PostgresMeetingsDao (PostgreSQL)
    """
    if Settings.use_postgres("meetings"):
        from database.postgres.collection_dao.meetings import PostgresMeetingsDao
        session = connection_manager.get_pg_session()
        dao = PostgresMeetingsDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.meetings import MeetingsDao
        return MeetingsDao(connection_manager.mongo_client)


def get_inbox_events_dao(connection_manager) -> Union["InboxEventsDao", "PostgresInboxEventsDao"]:
    """Get the appropriate InboxEvents DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        InboxEventsDao (MongoDB) or PostgresInboxEventsDao (PostgreSQL)
    """
    if Settings.use_postgres("inbox_events"):
        from database.postgres.collection_dao.inbox_events import PostgresInboxEventsDao
        session = connection_manager.get_pg_session()
        dao = PostgresInboxEventsDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.inbox_events import InboxEventsDao
        return InboxEventsDao(connection_manager.mongo_client)


def get_inbox_leads_dao(connection_manager) -> Union["InboxLeadsDao", "PostgresInboxLeadsDao"]:
    """Get the appropriate InboxLeads DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        InboxLeadsDao (MongoDB) or PostgresInboxLeadsDao (PostgreSQL)
    """
    if Settings.use_postgres("inbox_leads"):
        from database.postgres.collection_dao.inbox_events import PostgresInboxLeadsDao
        session = connection_manager.get_pg_session()
        dao = PostgresInboxLeadsDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.inbox_events import InboxLeadsDao
        return InboxLeadsDao(connection_manager.mongo_client)


def get_inbox_notes_dao(connection_manager) -> Union["InboxNotesDao", "PostgresInboxNotesDao"]:
    """Get the appropriate InboxNotes DAO based on feature flags.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        InboxNotesDao (MongoDB) or PostgresInboxNotesDao (PostgreSQL)
    """
    if Settings.use_postgres("inbox_notes"):
        from database.postgres.collection_dao.inbox_events import PostgresInboxNotesDao
        session = connection_manager.get_pg_session()
        dao = PostgresInboxNotesDao(session)
        if connection_manager.postgres_engine:
            dao.set_session_factory(connection_manager.postgres_engine.get_session)
        return dao
    else:
        from database.collection_dao.inbox_events import InboxNotesDao
        return InboxNotesDao(connection_manager.mongo_client)




# =============================================================================
# Tasks Module DAOs (PostgreSQL only - no MongoDB fallback)
# =============================================================================

def get_tasks_dao(connection_manager) -> "PostgresTasksDao":
    """Get the Tasks DAO.
    
    Tasks module is PostgreSQL-only.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        PostgresTasksDao
    """
    from database.postgres.collection_dao.tasks_dao import PostgresTasksDao
    session = connection_manager.get_pg_session()
    dao = PostgresTasksDao(session)
    if connection_manager.postgres_engine:
        dao.set_session_factory(connection_manager.postgres_engine.get_session)
    return dao


def get_task_type_policies_dao(connection_manager) -> "PostgresTaskTypePoliciesDao":
    """Get the TaskTypePolicy DAO.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        PostgresTaskTypePoliciesDao
    """
    from database.postgres.collection_dao.task_type_policies_dao import PostgresTaskTypePoliciesDao
    session = connection_manager.get_pg_session()
    dao = PostgresTaskTypePoliciesDao(session)
    if connection_manager.postgres_engine:
        dao.set_session_factory(connection_manager.postgres_engine.get_session)
    return dao


def get_task_activity_dao(connection_manager) -> "PostgresTaskActivityDao":
    """Get the TaskActivity DAO.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        PostgresTaskActivityDao
    """
    from database.postgres.collection_dao.task_activity_dao import PostgresTaskActivityDao
    session = connection_manager.get_pg_session()
    dao = PostgresTaskActivityDao(session)
    if connection_manager.postgres_engine:
        dao.set_session_factory(connection_manager.postgres_engine.get_session)
    return dao


def get_task_links_dao(connection_manager) -> "PostgresTaskLinksDao":
    """Get the TaskLinks DAO.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        PostgresTaskLinksDao
    """
    from database.postgres.collection_dao.task_links_dao import PostgresTaskLinksDao
    session = connection_manager.get_pg_session()
    dao = PostgresTaskLinksDao(session)
    if connection_manager.postgres_engine:
        dao.set_session_factory(connection_manager.postgres_engine.get_session)
    return dao


def get_deals_dao(connection_manager) -> "PostgresDealsDao":
    """Get the Deals DAO.
    
    Args:
        connection_manager: ConnectionManager instance
        
    Returns:
        PostgresDealsDao
    """
    from database.postgres.collection_dao.deals_dao import PostgresDealsDao
    session = connection_manager.get_pg_session()
    dao = PostgresDealsDao(session)
    if connection_manager.postgres_engine:
        dao.set_session_factory(connection_manager.postgres_engine.get_session)
    return dao
