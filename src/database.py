from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

# для докеров
DATABASE_URL = "postgresql+asyncpg://postgres:admin@db:5432/mblog_db"

# для локальной работы
# DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost:5432/mblog_db"

engine = create_async_engine(DATABASE_URL, echo=False)

LocalAsyncSession = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()
