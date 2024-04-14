import os
from typing import Optional

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src import models


async def test_get_user_me(client: AsyncClient):
    headers = {"api-key": "test"}
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["user"]["name"] == "Ivan"


async def test_get_user_id(client: AsyncClient):
    headers = {"api-key": "test"}
    response = await client.get("/api/users/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["user"]["name"] == "Ivan"


async def test_post_tweet(client: AsyncClient):
    headers = {"api-key": "test"}
    tweet = {"tweet_data": "Hi", "tweet_media_ids": [0]}
    response = await client.post("/api/tweets", headers=headers, json=tweet)
    assert response.status_code == 201
    assert response.json()["tweet_id"] == 1


async def test_post_tweet_db(event_loop, db_session: AsyncSession):
    query = await db_session.execute(
        select(models.Tweet).where(models.Tweet.id == 1)
    )
    data_tweet: models.Tweet = query.scalars().first()
    assert data_tweet.tweet_data == "Hi"


async def test_upload_file(client: AsyncClient):
    path_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(path_dir, "test_file.jpg")
    headers = {"api-key": "test"}
    files = {"file": (file_name, open(file_name, "rb"), "multipart/form-data")}
    response = await client.post("/api/medias", headers=headers, files=files)
    assert response.status_code == 201


async def test_upload_file_db(event_loop, db_session: AsyncSession):
    query = await db_session.execute(
        select(models.TweetMedia).where(models.TweetMedia.media_id == 1)
    )
    data_file: models.TweetMedia = query.scalars().first()
    assert "test_file.jpg" in data_file.name_file


async def test_post_likes_tweet(client: AsyncClient):
    headers = {"api-key": "test1"}
    response = await client.post(
        "/api/tweets/1/likes",
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["rusult"]


async def test_post_likes_tweet_db(event_loop, db_session: AsyncSession):
    query = await db_session.execute(select(models.LikesTweet))
    data_tweet_like: models.LikesTweet = query.scalars().first()
    assert data_tweet_like.tweet_id == 1


async def test_get_tweet(client: AsyncClient):
    headers = {"api-key": "test"}
    response = await client.get("/api/tweets", headers=headers)
    assert response.status_code == 200
    assert response.json()["tweets"][0]["id"] == 1


async def test_delete_likes_twee_bad(client: AsyncClient):
    headers = {"api-key": "test"}
    response = await client.delete("/api/tweets/1/likes", headers=headers)
    assert response.status_code == 400
    assert not response.json()["rusult"]


async def test_delete_likes_twee(client: AsyncClient):
    headers = {"api-key": "test1"}
    response = await client.delete("/api/tweets/1/likes", headers=headers)
    assert response.status_code == 200
    assert response.json()["rusult"]


async def test_delete_tweet(client: AsyncClient):
    headers = {"api-key": "test"}
    response = await client.delete("/api/tweets/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["rusult"]


async def test_delete_tweet_db(event_loop, db_session: AsyncSession):
    query = await db_session.execute(
        select(models.Tweet).where(models.Tweet.id == 1)
    )
    data_tweet: Optional[models.Tweet] = query.scalars().one_or_none()
    assert data_tweet is None


async def test_post_users_follow(client: AsyncClient):
    headers = {"api-key": "test3"}
    response = await client.post(
        "/api/users/1/follow",
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["rusult"]


async def test_post_users_follow_db(event_loop, db_session: AsyncSession):
    query = await db_session.execute(
        select(models.followers).where(models.followers.c.user_id == 4)
    )
    data_follow: models.followers = query.scalars().one_or_none()
    assert data_follow is not None


async def test_delete_users_follow(client: AsyncClient):
    headers = {"api-key": "test3"}
    response = await client.delete(
        "/api/users/1/follow",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["rusult"]


async def test_delete_users_follow_db(event_loop, db_session: AsyncSession):
    query = await db_session.execute(
        select(models.followers).where(models.followers.c.user_id == 4)
    )
    data_follow: models.followers = query.scalars().one_or_none()
    assert data_follow is None
