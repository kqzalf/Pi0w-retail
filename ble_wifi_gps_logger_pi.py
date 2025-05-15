"""Hybrid BLE + Wi-Fi + GPS Sensor Script with Wi-Fi Deauth and RF Jamming Detection"""

import asyncio
import subprocess
import time
import hashlib
import requests
import serial
import pynmea2
from bleak import BleakScanner
from bleak.exc import BleakError
from scapy.all import sniff, Dot11

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

def detect_deauth(packet):
    """Detect Wi-Fi deauthentication packets."""
    if packet.haslayer(Dot11):
        if packet.type == 0 and packet.subtype == 12:  # Deauthentication frame
            mac_address = packet.addr2
            print(f"[Deauth Detected] MAC: {mac_address}")
            return {"type": "deauth", "mac": mac_address}
    return None

def monitor_wifi_deauth():
    """Monitor for Wi-Fi deauthentication packets."""
    print("[*] Starting Wi-Fi deauth detection...")
    return sniff(iface="wlan0mon", prn=detect_deauth, store=0, timeout=10)

def detect_rf_jamming():
    """Detect RF jamming by analyzing noise levels."""
    try:
        output = subprocess.check_output(["iw", "dev", "wlan0", "station", "dump"], text=True)
        noise_levels = [int(line.split()[-1]) for line in output.splitlines() if "signal" in line]
        avg_noise = sum(noise_levels) / len(noise_levels) if noise_levels else -999
        if avg_noise < -90:  # Arbitrary threshold for jamming
            print("[RF Jamming Detected]")
            return {"type": "rf_jamming", "avg_noise": avg_noise}
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None

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
    except (BleakError, ValueError):
        return []

async def main():
    """Main logic to scan, tag, and send all signals."""
    timestamp = int(time.time())

    # Gather all data
    ble = await scan_ble()
    wifi = get_wifi_devices()
    gps = get_gps()
    deauth_packets = monitor_wifi_deauth()
    rf_jam = detect_rf_jamming()

    # Combine data
    all_data = ble + wifi
    if deauth_packets:
        all_data.extend(deauth_packets)
    if rf_jam:
        all_data.append(rf_jam)

    for d in all_data:
        d.update({"timestamp": timestamp, "sensor": SENSOR_ID, **gps})
    if all_data:
        try:
            requests.post(WEBHOOK_URL, json=all_data, headers=HEADERS, timeout=5)
        except requests.RequestException:
            pass

if __name__ == "__main__":
    asyncio.run(main())