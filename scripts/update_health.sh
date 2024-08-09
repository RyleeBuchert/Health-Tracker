#!/bin/bash

cd ~/Projects/Health-Tracker/
source .venv/bin/activate
cd ~/Projects/Health-Tracker/scripts/go_code/
./cronometer_download
cd ~/Projects/Health-Tracker/scripts/
python update_health.py
deactivate
cd ~
