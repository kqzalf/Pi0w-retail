"""Generate a BLE+WiFi heatmap using Folium."""
import pandas as pd
import folium
from folium.plugins import HeatMap
from datetime import datetime
import os

def generate_heatmap():
    db_path = "ble_logs.csv"
    if not os.path.exists(db_path):
        print("[!] No data file found.")
        return

    df = pd.read_csv(db_path)

    if "lat" not in df.columns or "lon" not in df.columns:
        print("[!] Missing lat/lon data.")
        return

    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        print("[!] No valid geolocation data.")
        return

    print(f"[+] Generating heatmap with {len(df)} points...")

    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=18)
    heat_data = df[["lat", "lon"]].values.tolist()
    HeatMap(heat_data).add_to(m)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"ble_heatmap_{now}.html"
    m.save(output_file)
    print(f"[✔] Heatmap saved to {output_file}")

if __name__ == "__main__":
    generate_heatmap()
