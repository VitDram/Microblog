from sqlalchemy import (
    ARRAY,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, object_session, relationship

# for docker
from src.database import Base

# for alembic
# from ..src.database import Base


followers = Table(
    "followers",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("following_id", ForeignKey("users.id"), primary_key=True),
    UniqueConstraint(
        "user_id", "following_id", name="idx_unique_user_following"
    ),
)


class LikesTweet(Base):
    __tablename__ = "likes_tweet"
    __table_args__ = (
        UniqueConstraint("user_id", "tweet_id", name="idx_unique_user_tweet"),
    )
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), primary_key=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    apy_key_user = Column(String, nullable=False)

    tweet = relationship("Tweet", back_populates="user")
    like_tweet = relationship(
        "Tweet",
        secondary="likes_tweet",
        back_populates="like_user",
        lazy="selectin",
    )

    following = relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.user_id == id),
        secondaryjoin=(followers.c.following_id == id),
        backref=backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )


class Tweet(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True, index=True)
    tweet_data = Column(String, nullable=False)
    tweet_media_ids = Column(ARRAY(Integer), default=[], nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="tweet")
    like_user = relationship(
        "User",
        secondary="likes_tweet",
        back_populates="like_tweet",
        lazy="selectin",
    )

    @hybrid_property
    def like_count(self):
        query = select(func.count(LikesTweet.tweet_id)).where(
            LikesTweet.tweet_id == self.id
        )
        result = object_session(self).execute(query)
        return result.scalars().one()

    @like_count.expression
    def like_count(cls):
        return (
            select(func.count(LikesTweet.tweet_id))
            .where(LikesTweet.tweet_id == cls.id)
            .label("like_count")
        )


class TweetMedia(Base):
    __tablename__ = "tweet_medias"
    media_id = Column(Integer, primary_key=True, index=True)
    name_file = Column(String, nullable=False)
