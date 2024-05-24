import datetime
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Sequence, Tuple, Union, Annotated

import uvicorn
from fastapi import Depends, FastAPI, Header, Request, Response, UploadFile, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src import models, schemas
from src.view_users import router as router_users
from src.database import LocalAsyncSession, engine
from src.utils import (
    add_data_to_db,
    add_file_media,
    add_like_tweet,
    create_tweet,
    delete_like_tweet,
    delete_tweets,
    get_user_id,
    get_user_me_from_db,
    out_tweets_user,
    user_following,
    user_unfollowing,
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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Создание сеанса базы данных
    :return: AsyncGenerator[AsyncSession, None]
        сеанс базы данных
    """
    async with LocalAsyncSession() as session:
        yield session


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


@app.post("/api/tweets", status_code=201, response_model=schemas.TweetOut)
async def post_api_tweets(
        tweet: schemas.TweetIn,
        api_key: Annotated[str, Header()],  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.TweetOut:
    """
    Добавление твита от имени текущего пользователя
    :param tweet: schemas.TweetIn
        содержание твита
    :param api_key: str
        ключ пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.UserOut
        данные пользователя и статус ответа
    """
    res: Union[str, int] = await create_tweet(
        session=session,
        apy_key_user=api_key,
        tweet_data=tweet.tweet_data,
        tweet_media_ids=tweet.tweet_media_ids,
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    return schemas.TweetOut(rusult=True, tweet_id=res)


@app.post("/api/medias", status_code=201, response_model=schemas.MediaOut)
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


@app.delete(
    "/api/tweets/{id}", status_code=200, response_model=schemas.ResultClass
)
async def delete_tweets_id(
        response: Response,
        id: Annotated[int, Path(gt=0)],
        api_key: Annotated[str, Header()],  # noqa: B008]
        session: AsyncSession = Depends(get_db),
) -> schemas.ResultClass:
    """
    Обработка запроса на удаление твита
    :param id: int
        ID твита
    :param api_key: str
        ключ пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.ResultClass
        статус ответа
    """
    res: Union[str, bool] = await delete_tweets(
        session=session, apy_key_user=api_key, id_tweet=id
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    elif not res:
        # попытка удалить не свой твит
        response.status_code = 400
    return schemas.ResultClass(rusult=res)


@app.post(
    "/api/tweets/{id}/likes",
    status_code=201,
    response_model=schemas.ResultClass,
)
async def post_tweet_likes(
        response: Response,
        id: Annotated[int, Path(gt=0)],
        api_key: Annotated[str, Header()],  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.ResultClass:
    """
    Обработка запроса на постановку отметки 'нравится' на твит
    :param id: int
        ID твита
    :param api_key: str
        ключ пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.ResultClass
        статус ответа
    """
    res: Union[str, bool] = await add_like_tweet(
        session=session, apy_key_user=api_key, id_tweet=id
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    elif not res:
        # попытка лайкнуть свой твит
        response.status_code = 400
    return schemas.ResultClass(rusult=res)


@app.delete(
    "/api/tweets/{id}/likes",
    status_code=200,
    response_model=schemas.ResultClass,
)
async def delete_tweet_likes(
        response: Response,
        id: Annotated[int, Path(gt=0)],
        api_key: Annotated[str, Header()],  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.ResultClass:
    """
    Обработка запроса на удаление отметки 'нравится' у твита
    :param id: int
        ID твита
    :param api_key: str
        ключ пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.ResultClass
        статус ответа
    """
    res: Union[str, bool] = await delete_like_tweet(
        session=session, apy_key_user=api_key, id_tweet=id
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    elif not res:
        # попытка удалить не свой лайк
        response.status_code = 400
    return schemas.ResultClass(rusult=res)


@app.get("/api/tweets", status_code=200, response_model=schemas.Tweets)
async def get_tweets_user(
        api_key: Annotated[str, Header()],  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.Tweets:
    """
    Обработка запроса на получение ленты с твитами
    :param api_key: str
        ключ пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.Tweets
        список твитов и статус ответа
    """
    res: Union[str, List[schemas.Tweet]] = await out_tweets_user(
        session=session, apy_key_user=api_key
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    return schemas.Tweets(rusult=True, tweets=res)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
