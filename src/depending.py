from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import LocalAsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Создание сеанса базы данных
    :return: AsyncGenerator[AsyncSession, None]
        сеанс базы данных
    """
    async with LocalAsyncSession() as session:
        yield session
