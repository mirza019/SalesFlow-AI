FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY backend ./backend
RUN pip install --no-cache-dir .
CMD ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"]

