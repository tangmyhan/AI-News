from celery import Celery

celery_app = Celery(
    "ainews_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=['processing.worker']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
)
