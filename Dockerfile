# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory in the container
WORKDIR /app

# Copy the script and any necessary files to the container
COPY raspi_image.py /app

# Install required Python libraries
RUN pip install --no-cache-dir boto3 requests git

# Install dependencies for sdm
RUN apt-get update && \
    apt-get install -y \
        sudo \
        curl \
        jq \
        rsync \
        parted \
        dosfstools \
        e2fsprogs \
        qemu-user-static \
        binfmt-support \
        kpartx \
        zip \
        unzip \
        pigz \
        xz-utils \
        gdisk \
        attr \
        libcap2-bin \
        python3 \
        python3-pip \
        python3-yaml \
        python3-requests && \
    rm -rf /var/lib/apt/lists/*

# Install sdm
RUN curl -L https://raw.githubusercontent.com/gitbls/sdm/master/EZsdmInstaller | bash


# Run the script with a door ID as an argument
CMD ["python", "raspi_image.py", "20"]
