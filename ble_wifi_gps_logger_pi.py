"""Hybrid BLE + Wi-Fi + GPS Sensor Script"""
import asyncio
import subprocess
import time
import hashlib
import requests
import json

from bleak import BleakScanner

SENSOR_ID = "HybridPi"
WEBHOOK_URL = "https://your-n8n-server.com/webhook/ble-data"
HEADERS = {"Content-Type": "application/json"}

def sha256(val):
    return hashlib.sha256(val.encode()).hexdigest()

def get_wifi_devices():
    try:
        output = subprocess.check_output(["sudo", "iw", "dev", "wlan0", "scan"], text=True, timeout=10)
        lines = output.splitlines()
        seen = []
        mac, signal = None, None
        for line in lines:
            line = line.strip()
            if line.startswith("BSS"):
                if mac:
                    seen.append({"mac_hash": sha256(mac), "rssi": signal, "type": "wifi"})
                mac = line.split()[1]
                signal = None
            elif "signal:" in line:
                signal = int(float(line.split("signal:")[1].split()[0]))
        if mac:
            seen.append({"mac_hash": sha256(mac), "rssi": signal, "type": "wifi"})
        return seen
    except Exception:
        return []

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
        return [{"mac_hash": sha256(d.address), "rssi": d.rssi, "type": "ble"} for d in devices]
    except:
        return []

async def main():
    timestamp = int(time.time())
    ble = await scan_ble()
    wifi = get_wifi_devices()
    gps = get_gps()
    all_data = ble + wifi
    for d in all_data:
        d.update({"timestamp": timestamp, "sensor": SENSOR_ID, **gps})
    if all_data:
        try:
            requests.post(WEBHOOK_URL, json=all_data, headers=HEADERS)
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
