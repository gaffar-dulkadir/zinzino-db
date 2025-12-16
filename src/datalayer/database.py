"""
PostgreSQL Database Manager for Chat Marketplace Service
Simplified working version based on previous project
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import text
from config import Config

class DatabaseManager:
    _instance = None
    _engine = None
    _session_local = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        try:
            config = Config()  # Artık singleton olduğu için güvenli
            self._engine = create_async_engine(
                f"postgresql+asyncpg://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/{config.postgres_db}",
                echo=False,  # Set to True for SQL logging
                pool_size=20,
                max_overflow=0
            )
            self._session_local = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
        except Exception as e:
            print(f"Error loading config: {e}")
            exit(1)
    
    @property
    def session_local(self):
        return self._session_local
    
    @property
    def engine(self):
        return self._engine
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session"""
        async with self._session_local() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> dict:
        """Simple health check"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                health_value = result.scalar()
                return {
                    "status": "healthy" if health_value == 1 else "unhealthy",
                    "database": "db_shell"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Singleton instance'ını oluştur
db_manager = DatabaseManager()

# Keep old names for compatibility
postgres_manager = db_manager

# Dependency for getting DB session
async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    async with db_manager.session_local() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Health check function
async def health_check() -> dict:
    """Convenience function for health check"""
    return await db_manager.health_check()

__all__ = [
    "DatabaseManager",
    "db_manager", 
    "postgres_manager",
    "get_postgres_session",
    "health_check"
]