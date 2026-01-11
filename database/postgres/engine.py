"""PostgreSQL database engine and session factory.

This module provides the SQLAlchemy async engine and session factory
for connecting to PostgreSQL.
"""

import os
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from database.postgres.models import Base


# Default database URL (can be overridden by environment variable)
DEFAULT_DATABASE_URL = "postgresql+asyncpg://agent_hub:agent_hub@localhost:5432/agent_hub"


class PostgresEngine:
    """PostgreSQL engine manager for async operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the PostgreSQL engine.
        
        Args:
            database_url: PostgreSQL connection URL. If not provided,
                         uses DATABASE_URL env var or default.
        """
        self._database_url = database_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        
    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return self._database_url
    
    @property
    def engine(self) -> AsyncEngine:
        """Get the SQLAlchemy async engine.
        
        Returns:
            AsyncEngine instance
            
        Raises:
            RuntimeError: If engine not initialized
        """
        if self._engine is None:
            raise RuntimeError("PostgreSQL engine not initialized. Call connect() first.")
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory.
        
        Returns:
            async_sessionmaker instance
            
        Raises:
            RuntimeError: If engine not initialized
        """
        if self._session_factory is None:
            raise RuntimeError("PostgreSQL engine not initialized. Call connect() first.")
        return self._session_factory
    
    async def connect(self, echo: bool = False, pool_size: int = 20, max_overflow: int = 30) -> None:
        """Initialize the database engine and session factory.
        
        Args:
            echo: If True, log all SQL statements
            pool_size: Number of connections in the pool
            max_overflow: Maximum overflow connections
        """
        if self._engine is not None:
            return  # Already connected
            
        # Create async engine with larger pool for concurrent API requests
        self._engine = create_async_engine(
            self._database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            pool_timeout=60,     # Increase timeout to 60 seconds
        )
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        
        print(f"✅ PostgreSQL engine connected to {self._database_url.split('@')[-1]}")
    
    async def disconnect(self) -> None:
        """Close the database engine and dispose of connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            print("✅ PostgreSQL engine disconnected")
    
    async def create_tables(self) -> None:
        """Create all database tables.
        
        This should only be used for development/testing.
        Use Alembic migrations for production.
        """
        if self._engine is None:
            raise RuntimeError("PostgreSQL engine not initialized. Call connect() first.")
            
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ PostgreSQL tables created")
    
    async def drop_tables(self) -> None:
        """Drop all database tables.
        
        WARNING: This will delete all data!
        """
        if self._engine is None:
            raise RuntimeError("PostgreSQL engine not initialized. Call connect() first.")
            
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            print("⚠️ PostgreSQL tables dropped")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session context manager.
        
        Usage:
            async with engine.session() as session:
                # Use session here
                
        Yields:
            AsyncSession instance
        """
        if self._session_factory is None:
            raise RuntimeError("PostgreSQL engine not initialized. Call connect() first.")
            
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    def get_session(self) -> AsyncSession:
        """Get a new session (caller must manage commit/rollback/close).
        
        Returns:
            AsyncSession instance
        """
        if self._session_factory is None:
            raise RuntimeError("PostgreSQL engine not initialized. Call connect() first.")
        return self._session_factory()


# Global engine instance (singleton pattern)
_postgres_engine: Optional[PostgresEngine] = None


def get_postgres_engine(database_url: Optional[str] = None) -> PostgresEngine:
    """Get or create the global PostgreSQL engine instance.
    
    Args:
        database_url: Optional database URL. Only used on first call.
        
    Returns:
        PostgresEngine instance
    """
    global _postgres_engine
    
    if _postgres_engine is None:
        _postgres_engine = PostgresEngine(database_url)
    
    return _postgres_engine


async def init_postgres(database_url: Optional[str] = None, echo: bool = False) -> PostgresEngine:
    """Initialize the PostgreSQL engine.
    
    Args:
        database_url: PostgreSQL connection URL
        echo: If True, log all SQL statements
        
    Returns:
        PostgresEngine instance
    """
    engine = get_postgres_engine(database_url)
    await engine.connect(echo=echo)
    return engine


async def close_postgres() -> None:
    """Close the PostgreSQL engine."""
    global _postgres_engine
    
    if _postgres_engine is not None:
        await _postgres_engine.disconnect()
        _postgres_engine = None


