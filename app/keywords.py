import os
import asyncio
from keybert import KeyBERT
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.models import Post
from app.celery import celery_app

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@blog_db/blog_db"
)
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def update_post_keywords(post_id: int, keywords: str):
    async with async_session() as db:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalars().first()
        if post:
            post.keywords = keywords
            await db.commit()


@celery_app.task
def generate_keywords(post_id: int, content: str):
    model = KeyBERT("roberta-base")
    keywords = model.extract_keywords(content, keyphrase_ngram_range=(1, 2), top_n=5)
    keywords_str = ", ".join([kw for kw, score in keywords])
    asyncio.run(update_post_keywords(post_id, keywords_str))
    return keywords_str
