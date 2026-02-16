#!/bin/bash

set -e  # Exit on any error

git pull
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
export FLASK_APP=run.py
flask db upgrade

systemctl restart calorie-tracker.socket
