from typing import List, Optional
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from app.auth import get_current_user
from app.db import get_db
from app.minio import get_minio_client, MINIO_BUCKET
from app.models import Media
from app.models import FavouritePost, Post, Comment
from io import BytesIO
from minio.error import S3Error
from datetime import datetime

router = APIRouter()

BASE_API_PATH = "/api/blog"


class PostBase(BaseModel):
    title: str
    content: str
    short_description: Optional[str] = None
    published: Optional[bool] = None
    keywords: Optional[str] = None


class PostCreate(PostBase):
    pass


class PostOut(PostBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class PostListOut(BaseModel):
    id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentOut(CommentBase):
    id: int
    post_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    pass


class UserOut(UserBase):
    id: int
    favorite_posts: List[PostOut] = []

    class Config:
        orm_mode = True


@router.post(
    BASE_API_PATH + "/posts/",
    response_model=PostOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: PostCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    new_post = Post(
        title=post.title,
        content=post.content,
        short_description=post.short_description,
        keywords=post.keywords,
        author_id=user["sub"],
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post


@router.get(BASE_API_PATH + "/posts/", response_model=List[PostListOut])
async def get_posts(_=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post)
        .options(load_only(Post.id, Post.title, Post.created_at, Post.updated_at))
        .where(Post.published == True)
    )  # type: ignore
    posts = result.scalars().all()
    return posts


@router.get(BASE_API_PATH + "/posts/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Post).where(
            Post.id == post_id,
            or_(Post.published == True, Post.author_id == user["sub"]),
        )
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post nie znaleziony")
    return post


@router.put(BASE_API_PATH + "/posts/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    post_update: PostCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.author_id == user["sub"])
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post nie znaleziony")
    post.title = post_update.title
    post.content = post_update.content
    post.short_description = post_update.short_description
    post.keywords = post_update.keywords
    post.published = post_update.published
    await db.commit()
    await db.refresh(post)
    return post


@router.delete(
    BASE_API_PATH + "/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_post(
    post_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.author_id == user["sub"])
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post nie znaleziony")
    await db.delete(post)
    await db.commit()
    return None


@router.post(
    BASE_API_PATH + "/posts/{post_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: int,
    comment: CommentCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post nie znaleziony")
    new_comment = Comment(
        content=comment.content, post_id=post_id, author_id=user["sub"]
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


@router.get(
    BASE_API_PATH + "/posts/{post_id}/comments", response_model=List[CommentOut]
)
async def get_comments(
    post_id: int, _=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Comment).filter(Comment.post_id == post_id))
    comments = result.scalars().all()
    return comments


@router.put(BASE_API_PATH + "/comments/{comment_id}", response_model=CommentOut)
async def update_comment(
    comment_id: int,
    comment_update: CommentCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id, Comment.author_id == user["sub"]
        )
    )
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Komentarz nie znaleziony")
    comment.content = comment_update.content
    await db.commit()
    await db.refresh(comment)
    return comment


@router.delete(
    BASE_API_PATH + "/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_comment(
    comment_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id, Comment.author_id == user["sub"]
        )
    )
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Komentarz nie znaleziony")
    await db.delete(comment)
    await db.commit()
    return None


@router.post(
    BASE_API_PATH + "/favorites/{post_id}",
    status_code=status.HTTP_200_OK,
)
async def add_favorite(
    post_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post nie znaleziony")

    result = await db.execute(
        select(FavouritePost).where(
            FavouritePost.user_id == user["sub"], FavouritePost.post_id == post_id
        )
    )
    existing_favorite = result.first()
    if existing_favorite:
        return {"message": "Post już znajduje się w ulubionych"}
    favourite = FavouritePost(user_id=user["sub"], post_id=post_id)
    db.add(favourite)

    await db.commit()
    return {"message": "Post dodany do ulubionych"}


@router.delete(
    BASE_API_PATH + "/favorites/{post_id}",
    status_code=status.HTTP_200_OK,
)
async def remove_favorite(
    post_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FavouritePost).where(
            FavouritePost.user_id == user["sub"], FavouritePost.post_id == post_id
        )
    )
    favorite = result.first()
    if not favorite:
        raise HTTPException(
            status_code=404, detail="Post nie znajduje się w ulubionych"
        )

    await db.execute(
        FavouritePost.delete().where(
            FavouritePost.user_id == user["sub"], FavouritePost.post_id == post_id
        )
    )
    await db.commit()
    return {"message": "Post usunięty z ulubionych"}


@router.post(BASE_API_PATH + "/upload/", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    post_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
    minio_client=Depends(get_minio_client),
):
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niedozwolony format pliku: {ext}",
        )

    unique_filename = f"{uuid.uuid4()}{ext}"

    try:
        file_data = await file.read()
        file_size = len(file_data)
        file_stream = BytesIO(file_data)
        minio_client.put_object(
            MINIO_BUCKET,
            unique_filename,
            file_stream,
            file_size,
            content_type=file.content_type,
        )
    except S3Error as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas uploadu do MinIO",
        )

    media_url = f"http://localhost:9000/{MINIO_BUCKET}/{unique_filename}"

    new_media = Media(post_id=post_id, file_path=unique_filename)
    db.add(new_media)
    await db.commit()
    await db.refresh(new_media)

    return {"url": media_url, "media_id": new_media.id}
