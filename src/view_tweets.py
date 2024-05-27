from typing import AsyncGenerator, List, Union, Annotated

from fastapi import APIRouter, Depends, Header, Response, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src import schemas
from src.database import LocalAsyncSession
from src.utils import (
    add_like_tweet,
    create_tweet,
    delete_like_tweet,
    delete_tweets,
    out_tweets_user,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Создание сеанса базы данных
    :return: AsyncGenerator[AsyncSession, None]
        сеанс базы данных
    """
    async with LocalAsyncSession() as session:
        yield session


class UnicornException(Exception):
    def __init__(self, result: bool, error_type: str, error_message: str):
        self.result: bool = result
        self.error_type: str = error_type
        self.error_message: str = error_message


router = APIRouter(
    prefix="/api/tweets",
    tags=["tweets"],
)

@router.post("/", status_code=201, response_model=schemas.TweetOut)
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


@router.delete(
    "/{id}", status_code=200, response_model=schemas.ResultClass
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


@router.post(
    "/{id}/likes",
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


@router.delete(
    "/{id}/likes",
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


# @router.get("/api/tweets", status_code=200, response_model=schemas.Tweets)
@router.get("/", status_code=200, response_model=schemas.Tweets)
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
