"""Database engine and session management.

Uses SQLAlchemy 2.0 async with psycopg3 driver (LangGraph's preferred PostgreSQL driver).
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from devascent.config import assessment_config

engine = create_async_engine(
    assessment_config.database_url,
    pool_size=10,
    max_overflow=20,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with async_session_maker() as session:
        yield session
