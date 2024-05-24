from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from src.config import setting

# для докеров
# DATABASE_URL = "postgresql+asyncpg://postgres:admin@db:5432/mblog_db"
DATABASE_URL = (
    f"postgresql+asyncpg://{setting.postgres_user}:{setting.postgres_password}@{setting.postgres_host}:"
    f"{setting.postgres_port}/{setting.postgres_db}"
)

# для локальной работы
# DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost:5432/mblog_db"

engine = create_async_engine(DATABASE_URL, echo=False)

LocalAsyncSession = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()
