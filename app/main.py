from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.es.index import init_indices
from app.es.instance import get_es_instance
from app.es.utils import wait_for_elasticsearch
from app.minio import init_minio_bucket
from app.routers import blog, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    es = get_es_instance()

    if not await wait_for_elasticsearch(es):
        raise Exception("Elasticsearch is not available after waiting")

    await init_indices(es)

    init_minio_bucket()

    yield


app = FastAPI(title="Blog", lifespan=lifespan)

app.include_router(blog.router)
app.include_router(metrics.router)
