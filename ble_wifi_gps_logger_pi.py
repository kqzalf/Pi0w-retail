"""Hybrid BLE + Wi-Fi + GPS Sensor Script"""

import asyncio
import subprocess
import time
import hashlib
import requests
import serial
import pynmea2
from bleak import BleakScanner

SENSOR_ID = "HybridPi"
WEBHOOK_URL = "https://your-n8n-server.com/webhook/ble-data"
HEADERS = {"Content-Type": "application/json"}


def sha256(val):
    """Hash MAC address using SHA-256."""
    return hashlib.sha256(val.encode()).hexdigest()


def get_wifi_devices():
    """Scan nearby Wi-Fi devices and hash their MACs."""
    try:
        output = subprocess.check_output(["sudo", "iw", "dev", "wlan0", "scan"], text=True, timeout=10)
        seen, mac, signal = [], None, None
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("BSS"):
                if mac:
                    seen.append({"mac_hash": sha256(mac), "rssi": signal, "type": "wifi"})
                mac = line.split()[1]
            elif "signal:" in line:
                try:
                    signal = int(float(line.split("signal:")[1].split()[0]))
                except ValueError:
                    continue
        if mac:
            seen.append({"mac_hash": sha256(mac), "rssi": signal, "type": "wifi"})
        return seen
    except (subprocess.SubprocessError, FileNotFoundError):
        return []


def get_gps():
    """Read GPS coordinates if GPS hardware is present."""
    try:
        ser = serial.Serial("/dev/ttyAMA0", 9600, timeout=1)
        while True:
            line = ser.readline().decode("ascii", errors="replace")
            if line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)
                return {"lat": msg.latitude, "lon": msg.longitude}
    except (serial.SerialException, pynmea2.ParseError):
        return {}


async def scan_ble():
    """Scan BLE devices and hash their MACs."""
    try:
        devices = await BleakScanner.discover(timeout=10.0)
        return [{"mac_hash": sha256(d.address), "rssi": d.rssi, "type": "ble"} for d in devices]
    except Exception:
        return []


async def main():
    """Main logic to scan, tag, and send all signals."""
    timestamp = int(time.time())
    ble = await scan_ble()
    wifi = get_wifi_devices()
    gps = get_gps()
    all_data = ble + wifi
    for d in all_data:
        d.update({"timestamp": timestamp, "sensor": SENSOR_ID, **gps})
    if all_data:
        try:
            requests.post(WEBHOOK_URL, json=all_data, headers=HEADERS, timeout=5)
        except requests.RequestException:
            pass


if __name__ == "__main__":
    asyncio.run(main())
