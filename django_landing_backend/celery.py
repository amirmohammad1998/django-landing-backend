import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_landing_backend.settings")

app = Celery("django_landing_backend")

app.conf.broker_url = os.getenv("CELERY_BROKER_URL")
app.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.timezone = "UTC"
app.conf.enable_utc = True

# Load all tasks from all apps
app.autodiscover_tasks()