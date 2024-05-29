from fastapi import APIRouter
from typing import List, Sequence, Tuple, Union, Annotated

from fastapi import Depends, Header, Response, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src import models, schemas
from src.depending import get_db
from src.exceptiions import UnicornException
from src.utils import (
    get_user_id,
    get_user_me_from_db,
    user_following,
    user_unfollowing,
)

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)


@router.get("/me", status_code=200, response_model=schemas.UserOut)
async def get_user_me(
        api_key: str = Header(None),  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.UserOut:
    """
    Пользователь может получить информацию о своём профиле
    :param api_key: str
        ключ пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.UserOut
        данные пользователя и статус ответа
    """
    res: Union[
        str, Tuple[models.User, Sequence[models.User], Sequence[models.User]]
    ] = await get_user_me_from_db(api_key, session)
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )

    me_data, following, followers = res
    user_followers: List[schemas.User] = [
        schemas.User(id=i_user.id, name=i_user.name) for i_user in followers
    ]
    user_following: List[schemas.User] = [
        schemas.User(id=i_user.id, name=i_user.name) for i_user in following
    ]
    user_me: schemas.UserAll = schemas.UserAll(
        id=me_data.id,
        name=me_data.name,
        followers=user_followers,
        following=user_following,
    )

    return schemas.UserOut(rusult=True, user=user_me)


@router.get("/{id}", status_code=200, response_model=schemas.UserOut)
async def get_user_id_(
        id: Annotated[int, Path(gt=0, description="Get user by ID")],
        session: AsyncSession = Depends(get_db)
) -> schemas.UserOut:
    """
    Обработка запроса на получение информацию о профиле пользователя по ID
    :param id: int
        ID пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.UserOut
        данные пользователя и статус ответа
    """
    res: Union[
        str, Tuple[models.User, Sequence[models.User], Sequence[models.User]]
    ] = await get_user_id(session, id)
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )

    me_data, following, followers = res

    user_followers: List[schemas.User] = [
        schemas.User(id=i_user.id, name=i_user.name) for i_user in followers
    ]
    user_following: List[schemas.User] = [
        schemas.User(id=i_user.id, name=i_user.name) for i_user in following
    ]
    user_me: schemas.UserAll = schemas.UserAll(
        id=me_data.id,
        name=me_data.name,
        followers=user_followers,
        following=user_following,
    )

    return schemas.UserOut(rusult=True, user=user_me)


@router.post(
    "/{id}/follow",
    status_code=201,
    response_model=schemas.ResultClass,
)
async def post_user_follow(
        response: Response,
        id: Annotated[int, Path(gt=0)],
        api_key: Annotated[str, Header()],  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.ResultClass:
    """
    Обработка запроса на добавление в друзья выбранного пользователя
    :param id: int
        ID выбранного пользователя
    :param api_key: str
        ключ текущего пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.ResultClass
        статус ответа
    """
    res: Union[str, bool] = await user_following(
        session=session, id_follower=id, apy_key_user=api_key
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    elif not res:
        # пользователь уже был добавлен в друзья
        response.status_code = 400
    return schemas.ResultClass(rusult=res)


@router.delete(
    "/{id}/follow",
    status_code=200,
    response_model=schemas.ResultClass,
)
async def delete_user_follow(
        response: Response,
        id: Annotated[int, Path(gt=0)],
        api_key: Annotated[str, Header()],  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.ResultClass:
    """
    Обработка запроса на удаление выбранного пользователя из друзей
    :param id: int
        ID выбранного пользователя
    :param api_key: str
        ключ текущего пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.ResultClass
        статус ответа
    """
    res: Union[str, bool] = await user_unfollowing(
        session=session, id_follower=id, apy_key_user=api_key
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    elif not res:
        response.status_code = 400
    return schemas.ResultClass(rusult=res)
