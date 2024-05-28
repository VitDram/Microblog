import os
from typing import List, Optional, Sequence, Tuple, Union

from sqlalchemy import and_, delete, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from src import models, schemas

API_KEY_DEFAULT = "test"


async def add_data_to_db(session: AsyncSession) -> None:
    """
    Создаёт таблицы в случае пустой БД
    :return: None
    """
    is_empty: bool = await check_user_is_empty(session)

    if is_empty:
        user_1: models.User = models.User(
            name="Ivan", apy_key_user=API_KEY_DEFAULT
        )
        user_2: models.User = models.User(
            name="Lena", apy_key_user=f"{API_KEY_DEFAULT}1"
        )
        user_3: models.User = models.User(
            name="Dasha", apy_key_user=f"{API_KEY_DEFAULT}2"
        )
        user_4: models.User = models.User(
            name="Petr", apy_key_user=f"{API_KEY_DEFAULT}3"
        )

        session.add_all([user_1, user_2, user_3, user_4])
        user_1.following.append(user_2)
        user_2.following.append(user_3)
        user_3.following.append(user_1)
        await session.commit()


async def check_user_is_empty(session: AsyncSession) -> bool:
    """
    Проверка наличия записей в таблицы Users
    :return: bool
        состояние таблицы (True: пустая, False: с данными)
    """
    query = await session.execute(select(models.User))
    res = query.scalars().first()
    return not bool(res)


async def get_user_by_apy_key(
        session: AsyncSession, apy_key_user: str
) -> Optional[models.User]:
    """
    Возвращает данные пользователя по ключу apy_key_user
    :param session: AsyncSession
        текущая сессия
    :param apy_key_user: str
        ключ пользователя
    :return: Optional[models.User]
        данные пользователя или None, если пользователь не найден
    """
    query = await session.execute(
        select(models.User).filter(models.User.apy_key_user == apy_key_user)
    )
    return query.scalars().first()


async def get_user_me_from_db(
        apy_key_user: Optional[str], session: AsyncSession
) -> Union[
    str, Tuple[models.User, Sequence[models.User], Sequence[models.User]]
]:
    """
    Возвращает данные текущего пользователя (для заполнения профиля)
    :param apy_key_user: Optional[str]
        ключ текущего пользователя, если не указан - первый в таблице Users
    :return: Union[
                str, Tuple[
                    models.User, Sequence[models.User], Sequence[models.User]
                    ]
                ]
        данные о пользователе, его подписчиках и подписках или об ошибке
    """
    if not apy_key_user:
        apy_key: str = API_KEY_DEFAULT
    else:
        apy_key = apy_key_user

    res: Optional[models.User] = await get_user_by_apy_key(session, apy_key)

    if not res:
        return (
            f"User not found & Пользователь с apy_key_user: "
            f"{apy_key} не найден"
        )

    # Выгрузка данных по подпискам и подписчикам
    query = await session.execute(res.following)
    following = query.scalars().all()
    query = await session.execute(res.followers)
    followers = query.scalars().all()

    return res, following, followers


async def get_user_id(
        session: AsyncSession, id_user: int
) -> Union[
    str, Tuple[models.User, Sequence[models.User], Sequence[models.User]]
]:
    """
    Возвращает данные пользователя по ID
    :param id_user: int
        ID пользователя в таблице User
    :return: Tuple[
            Optional[models.User],
            Optional[Sequence[models.User]],
            Optional[Sequence[models.User]]
            ]
        данные о пользователе, его подписчиках и подписках или None
    """
    res: Optional[models.User] = await session.get(models.User, id_user)
    if not res:
        return f"User not found & Пользователь с ID {id_user} не найден"

    # Выгрузка данных по подпискам и подписчикам
    query = await session.execute(res.following)
    following = query.scalars().all()
    query = await session.execute(res.followers)
    followers = query.scalars().all()

    return (res, following, followers)


async def create_tweet(
        session: AsyncSession,
        apy_key_user: str,
        tweet_data: str,
        tweet_media_ids: Optional[List[int]],
) -> Union[str, int]:
    """
    Добавляет новый твиттер в БД
    :param apy_key_user: str
        ключ пользователя
    :param tweet_data: str
        текстовое содержание твиттера
    :param tweet_media_ids: Optional[List[int]]
        список ID прикрепленных к твиттеру изображений (при наличии)
    :return: Union[str, int]
        ID созданного твиттера (при успешном добавлении в БД)
    """
    data_user: Optional[models.User] = await get_user_by_apy_key(
        session, apy_key_user
    )
    if not data_user:
        return (
            f"User not found & Пользователь с ключом "
            f"{apy_key_user} не найден"
        )
    new_tweet: models.Tweet = models.Tweet(
        tweet_data=tweet_data,
        tweet_media_ids=tweet_media_ids,
        user_id=data_user.id,
    )
    session.add(new_tweet)
    await session.commit()
    return new_tweet.id


async def add_file_media(
        session: AsyncSession, apy_key_user: str, name_file: str
) -> Union[str, int]:
    """
    Добавляет в БД имя прикрепленного к твиттеру файла
    :param apy_key_user: str
        ключ пользователя
    :param name_file: str
        имя файла
    :return: Union[str, int]
        ID новой записи (при успешном добавлении в БД)
    """
    new_media: models.TweetMedia = models.TweetMedia(name_file=name_file)
    data_user: Optional[models.User] = await get_user_by_apy_key(
        session, apy_key_user
    )
    if not data_user:
        return (
            f"User not found & Пользователь с ключом "
            f"{apy_key_user} не найден"
        )
    try:
        session.add(new_media)
    except SQLAlchemyError:
        await session.rollback()
        return "File not append & ошибка записи в БД"
    else:
        await session.commit()
    return new_media.media_id


async def delete_tweets(
        session: AsyncSession, apy_key_user: str, id_tweet: int
) -> Union[str, bool]:
    """
    Удаление твиттера пользователя по ID
    :param apy_key_user: str
        ключ пользователя
    :param id_tweet: int
        ID твиттера
    :return: Union[str, bool]
        статус выполнения операции
    """
    data_user: Optional[models.User] = await get_user_by_apy_key(
        session, apy_key_user
    )
    if not data_user:
        return (
            f"User not found & Пользователь с ключом "
            f"{apy_key_user} не найден"
        )

    # Проверяем принадлежность твитера пользователю
    query = await session.execute(
        select(models.Tweet).filter(
            and_(
                models.Tweet.user_id == data_user.id,
                models.Tweet.id == id_tweet,
            )
        )
    )
    tweet: Optional[models.Tweet] = query.scalars().one_or_none()
    if tweet:
        tweet_media_ids: List[int] = tweet.tweet_media_ids
        try:
            await session.delete(tweet)
        except SQLAlchemyError:
            await session.rollback()
            return False
        else:
            await session.commit()
            if len(tweet_media_ids) != 0:
                await delete_files_from_tweet(session, tweet_media_ids)
                stmt = delete(models.TweetMedia).filter(
                    models.TweetMedia.media_id.in_(tweet_media_ids)
                )
                await session.execute(stmt)
                await session.commit()
            return True
    else:
        return False


async def add_like_tweet(
        session: AsyncSession, apy_key_user: str, id_tweet: int
) -> Union[str, bool]:
    """
    Добавляет лайк твиттеру с указанным ID
    :param apy_key_user: str
        ключ пользователя
    :param id_tweet: int
        ID твиттера
    :return: Union[str, bool]
        статус выполнения операции
    """
    query = await session.execute(
        select(models.User)
        .where(models.User.apy_key_user == apy_key_user)
        .options(selectinload(models.User.like_tweet))
    )
    data_user: Optional[models.User] = query.scalars().first()
    if not data_user:
        return (
            f"User not found & Пользователь с ключом "
            f"{apy_key_user} не найден"
        )

    tweet: models.Tweet = await session.get(models.Tweet, id_tweet)
    # Проверка автора твита
    if tweet.user_id == data_user.id:
        return False

    try:
        data_user.like_tweet.append(tweet)
    except SQLAlchemyError:
        await session.rollback()
        return False
    else:
        await session.commit()
        return True


async def delete_like_tweet(
        session: AsyncSession, apy_key_user: str, id_tweet: int
) -> Union[str, bool]:
    """
    Удаляет лайк у твиттера с указанным ID
    :param apy_key_user: str
        ключ пользователя
    :param id_tweet: int
        ID твиттера
    :return: Union[str, bool]
        статус выполнения операции
    """
    data_user: Optional[models.User] = await get_user_by_apy_key(
        session, apy_key_user
    )
    if not data_user:
        return (
            f"User not found & Пользователь с ключом "
            f"{apy_key_user} не найден"
        )

    query = await session.execute(
        select(models.LikesTweet).filter(
            and_(
                models.LikesTweet.user_id == data_user.id,
                models.LikesTweet.tweet_id == id_tweet,
            )
        )
    )
    like_tweet: Optional[models.LikesTweet] = query.scalars().one_or_none()
    if like_tweet:
        try:
            await session.delete(like_tweet)
        except SQLAlchemyError:
            await session.rollback()
            return False
        else:
            await session.commit()
            return True
    else:
        return False


async def name_file_from_tweet_medias(
        session: AsyncSession, list_id_name_file: List[int]
) -> List[str]:
    """
    Возвращает список имен файлов по их ID из таблицы TweetMedia
    :param session: AsyncSession
        текущая сессия
    :param list_id_name_file: List[int]
        список ID имен файлов
    :return: List[str]
        список имен файлов, или пустой
    """
    list_name_file: List[str] = list()
    for i_id in list_id_name_file:
        res: Optional[models.TweetMedia] = await session.get(
            models.TweetMedia, i_id
        )
        if res:
            list_name_file.append(res.name_file)
    return list_name_file


async def user_following(
        session: AsyncSession, id_follower: int, apy_key_user: str
) -> Union[str, bool]:
    """
    Добавление подписчика пользователю
    :param id_follower: int
        ID подписчика
    :param apy_key_user: str
        ключ пользователя
    :return: Union[str, bool]
        статус выполнения операции
    """
    query = await session.execute(
        select(models.User).where(models.User.apy_key_user == apy_key_user)
    )

    data_user: Optional[models.User] = query.scalars().first()

    if not data_user:
        return (
            f"User not found & Пользователь с ключом "
            f"{apy_key_user} не найден"
        )

    # Поиск данных подписчика
    query = await session.execute(
        select(models.User).where(models.User.id == id_follower)
    )
    user_folower: Optional[models.User] = query.scalars().first()
    if not user_folower:
        return (
            f"User not found & Пользователь с ID " f"{id_follower} не найден"
        )

    try:
        data_user.following.append(user_folower)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return False
    else:
        return True


async def user_unfollowing(
        session: AsyncSession, id_follower: int, apy_key_user: str
) -> Union[str, bool]:
    """
    Удаление подписчика пользователю
    :param id_follower: int
        ID подписчика
    :param apy_key_user: str
        ключ пользователя
    :return: Union[str, bool]
        статус выполнения операции
    """
    query = await session.execute(
        select(models.User).where(models.User.apy_key_user == apy_key_user)
    )
    data_user: Optional[models.User] = query.scalars().first()
    if not data_user:
        return (
            f"User not found & Пользователь с ключом "
            f"{apy_key_user} не найден"
        )

    # Поиск данных подписчика
    query = await session.execute(
        select(models.User).where(models.User.id == id_follower)
    )
    user_folower: Optional[models.User] = query.scalars().first()
    if not user_folower:
        return (
            f"User not found & Пользователь с ID " f"{id_follower} не найден"
        )

    try:
        data_user.following.remove(user_folower)
    except SQLAlchemyError:
        session.rollback()
        return False
    else:
        await session.commit()
        return True


async def out_tweets_user(
        session: AsyncSession,
        apy_key_user: str,
) -> Union[str, List[schemas.Tweet]]:
    """
    Возвращает твиты в ленту пользователя
    :param apy_key_user: str
        ключ пользователя
    :return: Union[str, List[schemas.Tweet]]]
        список твиттов пользователя
    """
    data_user: Optional[models.User] = await get_user_by_apy_key(
        session, apy_key_user
    )
    if not data_user:
        return (
            f"User not found & Пользователь с ключом "
            f"{apy_key_user} не найден"
        )

    stmt = (
        select(models.Tweet)
        .options(
            joinedload(models.Tweet.user),
            selectinload(models.Tweet.like_user),
        )
        .order_by(desc(models.Tweet.like_count))
    )
    query = await session.execute(stmt)
    res = query.scalars().all()

    me_tweets: List[schemas.Tweet] = list()
    for i_res in res:  # type: models.Tweet
        id_tweet: int = i_res.id
        content_tweet: str = i_res.tweet_data
        author_tweet: schemas.User = schemas.User(
            id=i_res.user.id, name=i_res.user.name
        )

        likes_tweet: List[schemas.Like] = [
            schemas.Like(user_id=i_like.id, name=i_like.name)
            for i_like in i_res.like_user
        ]

        attachments_tweet: List[str] = await name_file_from_tweet_medias(
            session, i_res.tweet_media_ids
        )

        tweet: schemas.Tweet = schemas.Tweet(
            id=id_tweet,
            content=content_tweet,
            attachments=attachments_tweet,
            author=author_tweet,
            likes=likes_tweet,
        )
        me_tweets.append(tweet)

    return me_tweets


async def delete_files_from_tweet(
        session: AsyncSession, id_files_tweet: List[int]
) -> None:
    name_files: List[str] = await name_file_from_tweet_medias(
        session, id_files_tweet
    )
    for i_file in name_files:
        name_file: str = os.path.join("media", i_file)
        os.remove(name_file)
