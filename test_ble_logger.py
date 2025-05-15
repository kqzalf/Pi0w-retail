# test_ble_logger.py
# Minimal test harness to verify BLE scanning and DB logging

import asyncio
from bleak import BleakScanner
import time, hashlib, sqlite3
import os

DB = "test_ble_logs.db"
LOCATION = "TestPi"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scans (
        timestamp INTEGER, mac_hash TEXT, rssi INTEGER, sensor TEXT)''')
    conn.commit()
    conn.close()

async def test_scan_and_log():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=10.0)
    timestamp = int(time.time())
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for d in devices:
        mac_hash = hashlib.sha256(d.address.encode()).hexdigest()
        print(f"Device: {d.address}, RSSI: {d.rssi}, Hash: {mac_hash}")
        c.execute("INSERT INTO scans VALUES (?, ?, ?, ?)",
                  (timestamp, mac_hash, d.rssi, LOCATION))
    conn.commit()
    conn.close()
    print(f"Scan complete. Logged {len(devices)} devices to {DB}.")

if __name__ == "__main__":
    init_db()
    asyncio.run(test_scan_and_log())
