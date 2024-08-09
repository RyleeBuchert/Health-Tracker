#!/bin/bash

cd ~/Projects/Health-Tracker/
source .venv/bin/activate
if [ -f .env ]; then
  export $(cat .env | xargs)
fi
cd ~/Projects/Health-Tracker/scripts/go_code/
./cronometer_download
cd ~/Projects/Health-Tracker/scripts/
python update_health.py
deactivate
cd ~
