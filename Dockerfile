# Use an appropriate base image with Python 3
FROM ubuntu:20.04

# Install system dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        python3 \
        python3-pip \
        sudo \
        git \
        qemu-utils \
        qemu-user-static \
        coreutils \
        util-linux \
        kmod \
        dosfstools \
        e2fsprogs \
        udev \
        kpartx \
        parted \
        lvm2 \
        udisks2 \
        exfat-utils

# Install Python dependencies
RUN pip3 install boto3 requests

# Install sdm (Raspberry Pi SD Card Builder & Manager)
RUN git clone https://github.com/gitbls/sdm.git /opt/sdm && \
    cd /opt/sdm && \
    chmod +x ./install && \
    ./install

# Create necessary directories for EFS mount points
RUN mkdir -p /home/saguirregaray1/Documents/UM/tic/test/

# Copy your script into the container
COPY raspi_image.py /app/script.py

# Set the working directory
WORKDIR /app

# Set the command to run your script, passing the door_id from environment variables
CMD ["sh", "-c", "python3 script.py $DOOR_ID"]
