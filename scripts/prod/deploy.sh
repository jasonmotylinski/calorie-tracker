#!/bin/bash

set -e  # Exit on any error

git pull
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
export FLASK_APP=run.py
flask db upgrade

# Seed food database if the TSV is present and a re-import is needed.
# To trigger a re-import, create the flag file: touch data/.reimport_foods
TSV=data/opennutrition/opennutrition_foods.tsv
FLAG=data/.reimport_foods
if [ -f "$TSV" ] && [ -f "$FLAG" ]; then
  echo "Re-importing food database..."
  python scripts/import_opennutrition.py
  rm "$FLAG"
fi

systemctl restart calorie-tracker.socket
