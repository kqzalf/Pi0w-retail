# generate_heatmap.py
# Creates a heatmap from logged BLE scan data

import sqlite3
import pandas as pd
import folium
from folium.plugins import HeatMap
from datetime import datetime

# Config
DB_PATH = "ble_logs.db"
OUTPUT_HTML = "ble_heatmap.html"

# Static placeholder for Pi locations (mock coordinates, customize per sensor)
SENSOR_LOCATIONS = {
    "PiZero-East": (38.8977, -77.0365),
    "PiZero-West": (38.8976, -77.0375),
    "PiZero-North": (38.8980, -77.0360),
    "PiZero-South": (38.8974, -77.0360),
}

# Load and prepare data
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM scans", conn)
conn.close()

# Map hashed device hits to sensor coordinates
heatmap_points = []
for _, row in df.iterrows():
    sensor = row['sensor']
    if sensor in SENSOR_LOCATIONS:
        lat, lon = SENSOR_LOCATIONS[sensor]
        weight = max(1, 100 + int(row['rssi']))  # Convert RSSI to positive heat weight
        heatmap_points.append([lat, lon, weight])

# Create map
if heatmap_points:
    base = folium.Map(location=[38.8977, -77.0365], zoom_start=20)
    HeatMap(heatmap_points, radius=25, max_zoom=15).add_to(base)
    base.save(OUTPUT_HTML)
    print(f"Heatmap saved to {OUTPUT_HTML}")
else:
    print("No valid scan points found for heatmap.")
