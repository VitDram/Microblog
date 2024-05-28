import datetime
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Union, Annotated

import uvicorn
from fastapi import Depends, FastAPI, Header, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src import models, schemas
from src.view_users import router as router_users
from src.view_tweets import router as router_tweets
from src.database import LocalAsyncSession, engine
from src.depending import get_db
from src.utils import (
    add_data_to_db,
    add_file_media,
)


class UnicornException(Exception):
    def __init__(self, result: bool, error_type: str, error_message: str):
        self.result: bool = result
        self.error_type: str = error_type
        self.error_message: str = error_message


description = """
    API Microblogging helps you do awesome stuff. 🚀
    
    You will be able to:
    
    * **Read users**
    * **Create tweet**
    * **Remove tweet**
    * **Add and remove likes on tweets**
    * **Add and remove followers**
"""  # noqa: W293

PATH_PROJECT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_MEDIA: str = os.path.join(PATH_PROJECT, "media")


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


# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     """
#     Создание сеанса базы данных
#     :return: AsyncGenerator[AsyncSession, None]
#         сеанс базы данных
#     """
#     async with LocalAsyncSession() as session:
#         yield session


async def create_db_and_tables() -> None:
    """Создает базу данных и таблицы в ней"""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


@app.exception_handler(UnicornException)
async def unicorn_exception_handler(
        request: Request, exc: UnicornException
) -> JSONResponse:
    """Вывод информации об ошибке"""
    return JSONResponse(
        status_code=418,
        content={
            "result": exc.result,
            "error_type": exc.error_type,
            "error_message": exc.error_message,
        },
    )


@app.post("/api/medias", tags=["medias"], status_code=201, response_model=schemas.MediaOut)
async def post_medias(
        file: UploadFile,
        api_key: Annotated[str, Header()],  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.MediaOut:
    """
    Обработка запроса на загрузку файлов из твита
    :param file: str
        полное имя файла
    :param api_key: str
        ключ пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.MediaOut
        ID записи в таблице tweet_medias и статус ответа
    """

    file_name: str = str(datetime.datetime.now()) + "_" + file.filename

    if "test_file.jpg" in file.filename:
        file_path: str = "out_test.jpg"
    else:
        file_path: str = os.path.join(PATH_MEDIA, file_name)

    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())
    except Exception as exc:
        raise UnicornException(
            result=False, error_type="ErrorLoadFile", error_message=str(exc)
        )

    res: Union[str, int] = await add_file_media(
        session=session, apy_key_user=api_key, name_file=file_name
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    return schemas.MediaOut(rusult=True, media_id=res)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
