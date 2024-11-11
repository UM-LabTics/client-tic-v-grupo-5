#!/bin/bash

exec >> /home/grupo5pi/project.log 2>&1

HOME_DIR="/home/grupo5pi"
PROJECT_DIR="$HOME_DIR/project"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements2.txt"
PYTHON_SCRIPT="$PROJECT_DIR/main.py"
SQLITE_CREATION_SCRIPT="$PROJECT_DIR/create_sqlite.py"

echo "Checking virtual environment..."
# Check if the virtual environment already exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    # Create a virtual environment
    python3 -m venv $VENV_DIR
fi

# Activate the virtual environment
echo "Activating virtual environment..."
. $VENV_DIR/bin/activate

# Check if the required packages are already installed
echo "Check if req.txt..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "installing dependencies..."
    pip install -r $REQUIREMENTS_FILE
fi

if [ -f "$SQLITE_CREATION_SCRIPT" ]; then
    echo "Running sqlite creation script..."
    python $SQLITE_CREATION_SCRIPT
fi

celery -A $PROJECT_DIR/celery_project.celery_app worker --loglevel=info

# Check if the Python script exists and run it
echo "Run main script..."
if [ -f "$PYTHON_SCRIPT" ]; then
    echo "Running main..."
    python $PYTHON_SCRIPT
fi

# Deactivate the virtual environment
deactivate