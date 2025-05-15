# ble_wifi_gps_logger_pi.py
# Scans BLE and Wi-Fi devices, adds GPS if available, sends data to webhook

import asyncio
import subprocess
import time
import hashlib
import requests
import json
from bleak import BleakScanner

SENSOR_ID = "HybridPi-North"
WEBHOOK_URL = "https://your-n8n-server.com/webhook/ble-data"
POST_HEADERS = {"Content-Type": "application/json"}

def get_wifi_devices():
    try:
        result = subprocess.run(
            ["sudo", "iw", "dev", "wlan0", "scan"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
        output = result.stdout.splitlines()
        seen = []
        mac = None
        signal = None
        for line in output:
            line = line.strip()
            if line.startswith("BSS"):
                if mac:
                    seen.append({"mac_hash": sha256(mac), "rssi": signal, "type": "wifi"})
                mac = line.split()[1]
                signal = None
            elif "signal:" in line:
                signal = int(line.split("signal:")[1].split()[0])
        if mac:
            seen.append({"mac_hash": sha256(mac), "rssi": signal, "type": "wifi"})
        return seen
    except Exception as e:
        return []

def sha256(val):
    return hashlib.sha256(val.encode()).hexdigest()

def get_gps():
    try:
        import serial
        import pynmea2
        ser = serial.Serial("/dev/ttyAMA0", 9600, timeout=1)
        while True:
            line = ser.readline().decode("ascii", errors="replace")
            if line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)
                return {"lat": msg.latitude, "lon": msg.longitude}
    except Exception:
        return {}

async def scan_ble():
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        return [
            {"mac_hash": sha256(d.address), "rssi": d.rssi, "type": "ble"}
            for d in devices
        ]
    except:
        return []

async def main():
    timestamp = int(time.time())
    ble_results = await scan_ble()
    wifi_results = get_wifi_devices()
    gps_data = get_gps()
    all_data = ble_results + wifi_results
    for entry in all_data:
        entry.update({"timestamp": timestamp, "sensor": SENSOR_ID, **gps_data})

    if all_data:
        try:
            r = requests.post(WEBHOOK_URL, json=all_data, headers=POST_HEADERS)
            print("Posted", len(all_data), "entries:", r.status_code)
        except Exception as e:
            print("Upload failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
