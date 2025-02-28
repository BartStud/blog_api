import os
import uuid
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = os.getenv("MINIO_HOST", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio_access_key")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio_secret_key")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "blog-media")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)


def get_minio_client():
    return minio_client


def init_minio_bucket():
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        # przestawić na publiczny
