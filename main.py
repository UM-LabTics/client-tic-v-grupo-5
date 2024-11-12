import cv2
import os
from time import sleep
import logging

import RPi.GPIO as GPIO
from dotenv import load_dotenv

from celery_project.service import (
    get_filename,
    recognition,
)
from datetime import datetime, timedelta
from celery_project.tasks import mqtt_sender_task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def main():
    load_dotenv()

    cam_port = int(os.getenv("CAM_PORT"))
    photos_path = os.getenv("PHOTOS_PATH")
    door_id = os.getenv("DOOR_ID")

    button_pin = 27
    relay_pin = 16

    cam = cv2.VideoCapture(cam_port)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(relay_pin, GPIO.OUT)

    def send_new_access_log(access_result, authenticated_person_doc_id=None):
        publication_topic = f"device/{door_id}/logs"
        payload = {
            "data": {
                "timestamp": datetime.now().isoformat(),
                "is_successful": access_result,
                "door_id": door_id,
                "document_id": authenticated_person_doc_id,
            }
        }
        mqtt_sender_task.delay(publication_topic, payload)

    def send_alert():
        publication_topic = f"device/{door_id}/alert"
        payload = {
            "data": {
                "timestamp": datetime.now().isoformat(),
                "door_id": door_id
            }
        }
        sleep(3)
        mqtt_sender_task.delay(publication_topic, payload)

    # Failure tracking variables
    failure_count = 0
    first_failure_time = None

    try:
        logger.info("Press button to take picture")
        while True:
            ret, image = cam.read()
            if GPIO.input(button_pin) == GPIO.HIGH:
                logger.info("Button pressed. Capturing image.")
                filename = get_filename()
                image_path = os.path.join(photos_path, filename)
                cv2.imwrite(image_path, image)
                logger.info(f"Image saved to {image_path}")

                result, document_id = recognition(image)

                send_new_access_log(result, document_id)
                if result:
                    logger.info(f"Recognition successful for document ID {document_id}")
                    failure_count = 0
                    first_failure_time = None

                    GPIO.output(relay_pin, GPIO.HIGH)
                    logger.info("Access granted. Door opened.")
                    sleep(2)
                    GPIO.output(relay_pin, GPIO.LOW)
                else:
                    logger.warning("Recognition failed")
                    if first_failure_time is None:
                        first_failure_time = datetime.now()
                    failure_count += 1

                    if failure_count >= 3 and (datetime.now() - first_failure_time <= timedelta(minutes=1)):
                        send_alert()
                        logger.warning("Multiple failed access attempts detected. Alert sent.")
                        failure_count = 0
                        first_failure_time = None
                    elif datetime.now() - first_failure_time > timedelta(minutes=1):
                        failure_count = 1
                        first_failure_time = datetime.now()
            else:
                sleep(0.1)
    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        GPIO.cleanup()
        cam.release()

if __name__ == "__main__":
    main()
