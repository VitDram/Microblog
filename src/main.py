import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import models
from src.view_users import router as router_users
from src.view_tweets import router as router_tweets
from src.view_medias import router as router_medias
from src.database import LocalAsyncSession, engine
from src.exceptiions import UnicornException, unicorn_exception_handler
from src.utils import (
    add_data_to_db,
)

description = """
    API Microblogging helps you do awesome stuff. 🚀
    
    You will be able to:
    
    * **Read users**
    * **Create tweet**
    * **Remove tweet**
    * **Add and remove likes on tweets**
    * **Add and remove followers**
"""  # noqa: W293


async def create_db_and_tables() -> None:
    """Создает базу данных и таблицы в ней"""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Подготовка приложения к старту"""
    await create_db_and_tables()
    async with LocalAsyncSession() as session:
        await add_data_to_db(session)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="API_Microblogging",
    description=description,
    version="0.1.0",
    terms_of_service="http://example.com",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_users)
app.include_router(router_tweets)
app.include_router(router_medias)

app.add_exception_handler(UnicornException, unicorn_exception_handler)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
