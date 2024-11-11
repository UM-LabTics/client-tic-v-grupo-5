from time import sleep
import json
from celery import shared_task
from celery.signals import worker_shutdown

from contextlib import contextmanager
from threading import Event
import signal

from .celery_config import certs_path, mqtt_endpoint, subscription_topic_name
from .service import message_callback, get_mqtt_client

shutdown_event = Event()


@contextmanager
def register_signals():
    original_handlers = {}
    signals = [signal.SIGTERM, signal.SIGINT]

    for sig in signals:
        original_handlers[sig] = signal.signal(sig, signal_handler)

    try:
        yield
    finally:
        for sig, handler in original_handlers.items():
            signal.signal(sig, handler)


@worker_shutdown.connect
def worker_shutdown_handler(**kwargs):
    print("Celery worker shutdown signal received")
    shutdown_event.set()


@shared_task
def mqtt_sender_task(topic, payload):
    client = get_mqtt_client(certs_path, mqtt_endpoint)

    client.connect()

    dumped_payload = json.dumps(payload)

    client.publish(topic, dumped_payload, 1)

    client.disconnect()


def signal_handler(signum, frame):
    print(f"Received signal {signum}")
    shutdown_event.set()


@shared_task
def mqtt_listener_task():
    client = get_mqtt_client(certs_path, mqtt_endpoint)
    client.connect()
    client.subscribe(subscription_topic_name, 1, message_callback)

    try:
        print("Entering MQTT listener loop")
        with register_signals():
            while not shutdown_event.is_set():
                sleep(1)

    except Exception as e:
        print(f"Error in MQTT listener: {e}")
    finally:
        print("Disconnecting from MQTT client...")
        client.disconnect()
        shutdown_event.clear()
