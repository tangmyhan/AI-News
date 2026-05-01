from celery import Celery

celery_app = Celery(
    "ainews_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=['processing.worker', 'ingestion.producer']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    'crawl-news-every-1-hour': {
        'task': 'ingestion.run_crawler',
        'schedule': 3600.0, # 3600 giây = 1 giờ
    },
}
