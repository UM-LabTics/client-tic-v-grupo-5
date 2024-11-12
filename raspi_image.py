import argparse
import subprocess
from uuid import uuid4

import boto3
import requests

AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_REGION = ''
S3_BUCKET_NAME = ''
BACKEND_URL = ''

def notify_backend(presigned_url, door_id):
    try:
        print("Sending URL to backend...")
        request_url = f"{BACKEND_URL}/entity/doors/{door_id}/set_image_link"
        response = requests.post(request_url, json={'image_link': presigned_url})
        response.raise_for_status()
        print("Backend notified successfully.")
    except Exception as e:
        print(f"Failed to notify backend: {e}")

def customize_image(new_image,thing_name):
    command = [
        "sudo", "sdm", "--customize", new_image, "--extend", "--xmb", "1000",
        "--plugin", "user:deluser=pi",
        "--plugin", "user:adduser=grupo5pi|password=raspi",
        "--plugin", "mkdir:dir=/home/grupo5pi/project|chown=grupo5pi:grupo5pi|chmod=700",
        "--plugin", "mkdir:dir=/home/grupo5pi/venvs|chown=grupo5pi:grupo5pi|chmod=700",
        "--plugin", "mkdir:dir=/home/grupo5pi/certs|chown=grupo5pi:grupo5pi|chmod=700",
        "--plugin", "mkdir:dir=/home/grupo5pi/photos|chown=grupo5pi:grupo5pi|chmod=700",
        "--plugin", "network:netman=nm|wificountry=UY|nmconn=Aguirregaray.nmconnection",
        "--plugin", "disables:piwiz|triggerhappy",
        "--plugin", "L10n:host",
        "--plugin", "apps:apps=@baseapps.txt|name=base",
        "--plugin", "apps:apps=@pythonapps.txt|name=python",
        "--plugin", "apps:apps=@libraries.txt|name=libraries",
        "--plugin", "copydir:from=/home/saguirregaray1/Documents/UM/tic/test/celery_project|to=/home/grupo5pi/project/",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/.env|to=/home/grupo5pi/project|mkdirif",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/requirements.txt|to=/home/grupo5pi/project|mkdirif",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/requirements2.txt|to=/home/grupo5pi/project|mkdirif",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/main.py|to=/home/grupo5pi/project|mkdirif",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/create_sqlite.py|to=/home/grupo5pi/project|mkdirif",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/root-CA.crt|to=/home/grupo5pi/certs|mkdirif",
        "--plugin", f"copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/{thing_name}.cert.pem|to=/home/grupo5pi/certs|mkdirif",
        "--plugin", f"copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/{thing_name}.private.key|to=/home/grupo5pi/certs|mkdirif",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/runatstartup.sh|to=/home/grupo5pi/project|mkdirif",
        "--plugin", "system:service-enable=rc-local",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/startup.service|to=/etc/systemd/system/|mkdirif",
        "--plugin", "copyfile:from=/home/saguirregaray1/Documents/UM/tic/test/rc.local|to=/etc/",
        "--plugin", "system:service-enable=startup.service|name=startup",
        "--batch",
        "--expand-root",
        "--restart"
    ]

    # Run the command
    subprocess.run(command,check=True)
    print("Image customization completed successfully.")

def edit_env(door_id, thing_name):
    with open('.env', 'r') as file:
        lines = file.readlines()

    with open('.env', 'w') as file:
        for line in lines:
            if line.startswith('DOOR_ID='):
                file.write(f'DOOR_ID={door_id}\n')
            elif line.startswith('THING_NAME='):
                file.write(f'THING_NAME={thing_name}\n')
            else:
                file.write(line)


def create_files(thing_name,certificate_pem, private_key):
    with open(f'{thing_name}.cert.pem', 'w') as cert_file:
        cert_file.write(certificate_pem)

    with open(f'{thing_name}.private.key', 'w') as priv_file:
        priv_file.write(private_key)

def get_new_image_path():
    new_file_name = f"{str(uuid4())}.img"
    subprocess.run(['cp', 'raspberry_base.img', new_file_name], check=True)
    return new_file_name

def upload_to_s3(file_path, bucket_name, object_name):
    s3_client = boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    try:
        print("Uploading image to S3...")
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"Image successfully uploaded to S3 as '{object_name}' in bucket '{bucket_name}'.")

        # Generate a presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=36000  # URL expiration time in seconds
        )
        return presigned_url
    except Exception as e:
        print(f"Failed to upload image to S3: {e}")
        return None

def main(door_id):
    try:
        thing_name = f"puerta_{door_id}"
        edit_env(door_id, thing_name)

        iot_client = boto3.client(
            'iot',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

        response = iot_client.create_keys_and_certificate(setAsActive=True)

        certificate_arn = response.get("certificateArn")

        iot_client.attach_policy(
            policyName='general_door_policy',
            target=certificate_arn
        )

        certificate_pem = response['certificatePem']
        private_key = response['keyPair']['PrivateKey']

        create_files(thing_name,certificate_pem, private_key)

        new_image = get_new_image_path()
        customize_image(new_image, thing_name)

        presigned_url = upload_to_s3(new_image, S3_BUCKET_NAME, f"images/{new_image}")

        print(f"presigned url: {presigned_url}")
        if presigned_url:
            notify_backend(presigned_url, door_id)

    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Door id')
    parser.add_argument('door_id', type=str, help='The door id')
    args = parser.parse_args()
    main(args.door_id)