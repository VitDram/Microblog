import asyncio
from typing import AsyncGenerator, Generator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine, AsyncEngine)
from sqlalchemy_utils import create_database, database_exists

from src.database import Base
from src.main import app
from src.depending import get_db
from src.utils import add_data_to_db

# for test with local db
# SQLALCHEMY_DATABASE_URL = (
#   "postgresql+asyncpg://test:test@localhost:5432/testdb"
# )

SQLALCHEMY_DATABASE_URL = (
    "postgresql+asyncpg://test:test@localhost:5438/testdb"
)


@pytest_asyncio.fixture(scope="session")
def event_loop(request) -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Создаем экземпляр цикла обработки событий для каждого тестового примера.
    """
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine: AsyncEngine= create_async_engine(SQLALCHEMY_DATABASE_URL)

    if not database_exists:
        create_database(engine.url)

    yield engine


@pytest_asyncio.fixture(scope="session")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async with db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

        TestingSessionLocal = async_sessionmaker(
            db_engine, expire_on_commit=False
        )

        async with TestingSessionLocal(bind=connection) as session:
            await add_data_to_db(session)
            yield session
            await session.flush()
            await session.rollback()


@pytest_asyncio.fixture(scope="function")
def override_get_db(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest_asyncio.fixture(scope="function")
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
