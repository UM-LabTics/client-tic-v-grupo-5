from celery.signals import worker_ready
from celery_project.tasks import mqtt_listener_task

@worker_ready.connect
def at_start(sender, **kwargs):
    print("Starting MQTT listener task...")
    mqtt_listener_task.delay()
