import os
from celery import Celery

def make_celery(app_name=__name__):
    backend = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    broker = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return Celery(app_name, backend=backend, broker=broker)

celery_app = make_celery()
