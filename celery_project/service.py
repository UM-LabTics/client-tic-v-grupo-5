from datetime import datetime
import json
import sqlite3
import os
import uuid

import cv2
import numpy as np
import face_recognition
import requests

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

from .celery_config import db_name, photos_path, door_id, thing_name


def recognition(taken_image):

    known_face_encodings, known_face_doc_ids = load_known_faces()

    rgb_image = cv2.cvtColor(taken_image, cv2.COLOR_BGR2RGB)

    # Resize image for faster processing (optional)
    # rgb_image = cv2.resize(rgb_image, (0, 0), fx=0.5, fy=0.5)

    face_locations = face_recognition.face_locations(rgb_image)
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

    if not face_encodings:
        print("No faces found in the image.")
        return False, None

    face_encoding = face_encodings[0]

    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
    best_match_index = np.argmin(face_distances)
    if matches[best_match_index]:
        doc_id = known_face_doc_ids[best_match_index]
        print(f"Found {doc_id} in the image.")
        return True, doc_id
    else:
        print("Face not recognized.")
        return False, None


def load_known_faces():
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT document_id, encoding FROM people")
    rows = cursor.fetchall()
    connection.close()

    known_face_encodings = []
    known_face_doc_ids = []

    for doc_id, encoding_bytes in rows:
        face_encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
        known_face_encodings.append(face_encoding)
        known_face_doc_ids.append(doc_id)

    return known_face_encodings, known_face_doc_ids


def get_encoding(photo_path):
    image = face_recognition.load_image_file(photo_path)

    encodings = face_recognition.face_encodings(image)
    if not encodings:
        print("No face found in the image.")
        return False

    face_encoding = encodings[0]
    encoding_bytes = face_encoding.tobytes()

    return encoding_bytes


def download_file_from_s3(s3_url):

    os.makedirs(photos_path, exist_ok=True)

    file_name = s3_url.split("/")[-1].split("?")[0]
    save_path = os.path.join(photos_path, file_name)

    try:
        response = requests.get(s3_url)
        response.raise_for_status()

        with open(save_path, "wb") as file:
            file.write(response.content)

        print(f"File downloaded successfully to {save_path}")
        return save_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        return None


def insert_person(person_data, photo_url):
    photo_path = download_file_from_s3(photo_url)

    encoding_bytes = get_encoding(photo_path)

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    cursor.execute(
        """
    INSERT INTO people (name, document_id, photo, encoding)
    VALUES (?, ?, ?, ?)
    """,
        (person_data[1], person_data[2], photo_path, encoding_bytes),
    )

    connection.commit()
    connection.close()
    print(
        f"Inserted person {person_data[1]} with document ID {person_data[2]} into the database."
    )


def message_callback(client, userdata, message):
    print(
        f"Received message from topic: {message.topic}: {message.payload.decode('utf-8')}"
    )

    data = json.loads(message.payload.decode("utf-8"))

    person_data = data.get("body")
    photo_url = data.get("url")

    if data.get("door_id") == int(door_id):
        insert_person(person_data, photo_url)


def get_mqtt_client(certs_path, mqtt_endpoint):
    client = AWSIoTMQTTClient(thing_name)

    ca_path = f"{certs_path}/root-CA.crt"
    cert_path = f"{certs_path}/{thing_name}.cert.pem"
    key_path = f"{certs_path}/{thing_name}.private.key"

    client.configureEndpoint(mqtt_endpoint, 8883)
    client.configureCredentials(ca_path, key_path, cert_path)

    client.configureAutoReconnectBackoffTime(1, 32, 20)
    client.configureOfflinePublishQueueing(-1)
    client.configureDrainingFrequency(2)
    client.configureConnectDisconnectTimeout(10)
    client.configureMQTTOperationTimeout(5)

    return client


def get_filename():
    auto_id = str(uuid.uuid4())
    date = datetime.now()
    return f"{auto_id}_{date}.jpg"
