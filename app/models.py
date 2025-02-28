import keyword
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    short_description = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    published_at = Column(DateTime, nullable=True)
    keywords = Column(String, nullable=True)
    comments = relationship("Comment", back_populates="post", cascade="all, delete")
    favorited_by = relationship("FavouritePost", back_populates="post")
    media = relationship("Media", back_populates="post", cascade="all, delete")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(String, nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    post = relationship("Post", back_populates="comments")


class FavouritePost(Base):
    __tablename__ = "favorite_posts"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(String, nullable=False)
    post = relationship("Post", back_populates="favorited_by")


class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    post = relationship("Post", back_populates="media")
