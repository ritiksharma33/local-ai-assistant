import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Define a clean local SQLite file path path inside your project directory
DATABASE_URL = "sqlite+aiosqlite:///./telemetry_records.db"

# Create the asynchronous engine to handle database connections without blocking the event loop
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Generate a thread-safe factory configuration for processing individual transactions
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency provider to cleanly inject db sessions into FastAPI endpoints
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()