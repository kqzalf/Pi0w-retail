#!/bin/bash
# Schedule this with cron: runs heatmap generation every 6 hours

cd /home/pi/ble-foot-traffic-logger
/usr/bin/python3 generate_heatmap.py >> heatmap.log 2>&1
