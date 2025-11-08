from celery import shared_task
from django.db import IntegrityError
from landing.models import Subscriber
from logs.models import RequestLog
from logs.utils import insert_log_to_mongo


@shared_task(bind=True, max_retries=3)
def save_phone_async(
    self,
    phone: str,
    ip: str = None,
    user_agent: str = None,
    referrer: str = None,
    request_id: str = None,
):
    """
    Celery task responsible for storing phone and logging the event.
    """
    try:
        Subscriber.objects.get_or_create(phone=phone)
        pg_status = "success"
    except IntegrityError:
        pg_status = "duplicate"
    except Exception as e:
        pg_status = f"error: {str(e)}"

    # Create and log to MongoDB
    log_entry = RequestLog(phone=phone, ip=ip, user_agent=user_agent, pg_status=pg_status, referrer=referrer,
                           request_id=request_id)
    insert_log_to_mongo(log_entry)

    return {"pg_status": pg_status}