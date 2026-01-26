# src/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import get_settings

settings = get_settings()

# 1. Create the Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set True to see SQL queries in logs
    future=True,
    connect_args={"check_same_thread": False} # Needed for SQLite only
)

# 2. Create the Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# 3. Base Class for Models
Base = declarative_base()

# 4. Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()