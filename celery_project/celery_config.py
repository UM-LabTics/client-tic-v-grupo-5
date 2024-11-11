from celery import Celery

from dotenv import load_dotenv
import os

load_dotenv()

door_id = os.getenv("DOOR_ID")
thing_name = os.getenv("THING_NAME")
certs_path = os.getenv("CERTS_PATH")
mqtt_endpoint = os.getenv("MQTT_ENDPOINT")

subscription_topic_name = os.getenv("SUBSCRIPTION_TOPIC_NAME")

db_name = os.getenv("DB_NAME")

photos_path = os.getenv("PHOTOS_PATH")

# Initialize Celery with Redis as the message broker
app = Celery("mqtt_task", broker="redis://localhost:6379/0")

# Configuration options (you can add more as needed)
app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

app.autodiscover_tasks(["celery_project"])

import celery_project.signals
