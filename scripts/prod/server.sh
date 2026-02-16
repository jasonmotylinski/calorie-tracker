#!/usr/bin/env bash
cd /var/projects/calorie-tracker
source venv/bin/activate
exec gunicorn --bind unix:/run/calorie-tracker.sock run:app
