import os
from celery import Celery

def make_celery(app_name=__name__):
    backend = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    broker = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    app = Celery(app_name, backend=backend, broker=broker)
    # Fail fast when broker is unreachable (dev without Redis)
    app.conf.update(
        broker_connection_retry=False,
        broker_connection_timeout=1,
        broker_transport_options={"socket_connect_timeout": 1, "socket_timeout": 1},
    )
    return app

celery_app = make_celery()
