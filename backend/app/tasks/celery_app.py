from celery import Celery
celery_app = Celery("salesflow", broker="redis://redis:6379/0", backend="redis://redis:6379/1")

