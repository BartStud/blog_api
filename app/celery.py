import os
from celery import Celery

celery_app = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//"),
    backend="rpc://",
)
