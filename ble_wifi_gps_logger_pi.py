"""Hybrid BLE + Wi-Fi + GPS Sensor Script with Wi-Fi Deauth and RF Jamming Detection.

This module provides functionality to scan for BLE and Wi-Fi devices, detect GPS coordinates,
monitor for Wi-Fi deauthentication attacks, and detect RF jamming. All data is sent to a
configured webhook endpoint.
"""

import asyncio
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import hashlib
import requests
import serial
import pynmea2
from bleak import BleakScanner
from bleak.exc import BleakError
from scapy.all import sniff, Dot11

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration settings for the sensor."""
    # Core settings
    SENSOR_ID: str = os.getenv('SENSOR_ID', 'HybridPi')
    WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', 'https://your-n8n-server.com/webhook/ble-data')
    HEADERS: Dict[str, str] = {"Content-Type": "application/json"}
    
    # Hardware settings
    GPS_PORT: str = os.getenv('GPS_PORT', '/dev/ttyAMA0')
    GPS_BAUDRATE: int = int(os.getenv('GPS_BAUDRATE', '9600'))
    WIFI_INTERFACE: str = os.getenv('WIFI_INTERFACE', 'wlan0')
    WIFI_MONITOR_INTERFACE: str = os.getenv('WIFI_MONITOR_INTERFACE', 'wlan0mon')
    
    # Detection thresholds
    RF_JAMMING_THRESHOLD: int = int(os.getenv('RF_JAMMING_THRESHOLD', '-90'))
    SCAN_TIMEOUT: int = int(os.getenv('SCAN_TIMEOUT', '10'))
    BURST_THRESHOLD: int = int(os.getenv('BURST_THRESHOLD', '10'))
    LOW_TRAFFIC_THRESHOLD: int = int(os.getenv('LOW_TRAFFIC_THRESHOLD', '2'))
    
    # GPS settings
    GPS_ENABLED: bool = os.getenv('GPS_ENABLED', 'true').lower() == 'true'
    GPS_DRIFT_THRESHOLD: float = float(os.getenv('GPS_DRIFT_THRESHOLD', '0.001'))  # ~100m in degrees
    
    # Alert settings
    ALERT_ON_BURST: bool = os.getenv('ALERT_ON_BURST', 'true').lower() == 'true'
    ALERT_ON_LOW_TRAFFIC: bool = os.getenv('ALERT_ON_LOW_TRAFFIC', 'true').lower() == 'true'
    ALERT_ON_GPS_DRIFT: bool = os.getenv('ALERT_ON_GPS_DRIFT', 'true').lower() == 'true'

config = Config()

def sha256(val: str) -> str:
    """Hash MAC address using SHA-256.
    
    Args:
        val: The MAC address to hash
        
    Returns:
        The SHA-256 hash of the MAC address
    """
    return hashlib.sha256(val.encode()).hexdigest()

def get_wifi_devices() -> List[Dict[str, Union[str, int]]]:
    """Scan nearby Wi-Fi devices and hash their MACs.
    
    Returns:
        List of dictionaries containing hashed MAC addresses, RSSI values, and device type
    """
    try:
        output = subprocess.check_output(
            ["sudo", "iw", "dev", config.WIFI_INTERFACE, "scan"],
            text=True,
            timeout=config.SCAN_TIMEOUT
        )
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
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse signal strength: {e}")
                    continue
        if mac:
            seen.append({"mac_hash": sha256(mac), "rssi": signal, "type": "wifi"})
        return seen
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Wi-Fi scan failed: {e}")
        return []

def detect_deauth(packet: Dot11) -> Optional[Dict[str, str]]:
    """Detect Wi-Fi deauthentication packets.
    
    Args:
        packet: The captured network packet
        
    Returns:
        Dictionary containing deauth information if detected, None otherwise
    """
    if packet.haslayer(Dot11):
        if packet.type == 0 and packet.subtype == 12:  # Deauthentication frame
            mac_address = packet.addr2
            logger.warning(f"[Deauth Detected] MAC: {mac_address}")
            return {"type": "deauth", "mac": mac_address}
    return None

def monitor_wifi_deauth() -> List[Dict[str, str]]:
    """Monitor for Wi-Fi deauthentication packets.
    
    Returns:
        List of detected deauthentication events
    """
    logger.info("[*] Starting Wi-Fi deauth detection...")
    try:
        return sniff(
            iface=config.WIFI_MONITOR_INTERFACE,
            prn=detect_deauth,
            store=0,
            timeout=config.SCAN_TIMEOUT
        )
    except Exception as e:
        logger.error(f"Failed to monitor Wi-Fi deauth: {e}")
        return []

def detect_rf_jamming() -> Optional[Dict[str, Union[str, float]]]:
    """Detect RF jamming by analyzing noise levels.
    
    Returns:
        Dictionary containing jamming information if detected, None otherwise
    """
    try:
        output = subprocess.check_output(
            ["iw", "dev", config.WIFI_INTERFACE, "station", "dump"],
            text=True
        )
        noise_levels = [
            int(line.split()[-1])
            for line in output.splitlines()
            if "signal" in line
        ]
        if not noise_levels:
            return None
            
        avg_noise = sum(noise_levels) / len(noise_levels)
        if avg_noise < config.RF_JAMMING_THRESHOLD:
            logger.warning("[RF Jamming Detected]")
            return {"type": "rf_jamming", "avg_noise": avg_noise}
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"RF jamming detection failed: {e}")
    return None

def get_gps() -> Dict[str, float]:
    """Read GPS coordinates if GPS hardware is present.
    
    Returns:
        Dictionary containing latitude and longitude if available
    """
    try:
        with serial.Serial(
            config.GPS_PORT,
            config.GPS_BAUDRATE,
            timeout=1
        ) as ser:
            for _ in range(10):  # Try up to 10 times
                line = ser.readline().decode("ascii", errors="replace")
                if line.startswith("$GPGGA"):
                    msg = pynmea2.parse(line)
                    return {"lat": msg.latitude, "lon": msg.longitude}
    except (serial.SerialException, pynmea2.ParseError) as e:
        logger.error(f"GPS reading failed: {e}")
    return {}

async def scan_ble() -> List[Dict[str, Union[str, int]]]:
    """Scan BLE devices and hash their MACs.
    
    Returns:
        List of dictionaries containing hashed MAC addresses, RSSI values, and device type
    """
    try:
        devices = await BleakScanner.discover(timeout=config.SCAN_TIMEOUT)
        return [
            {
                "mac_hash": sha256(d.address),
                "rssi": d.rssi,
                "type": "ble"
            }
            for d in devices
        ]
    except (BleakError, ValueError) as e:
        logger.error(f"BLE scan failed: {e}")
        return []

async def main() -> None:
    """Main logic to scan, tag, and send all signals."""
    timestamp = int(time.time())

    # Gather all data
    ble = await scan_ble()
    wifi = get_wifi_devices()
    gps = get_gps() if config.GPS_ENABLED else {}
    deauth_packets = monitor_wifi_deauth()
    rf_jam = detect_rf_jamming()

    # Combine data
    all_data = ble + wifi
    if deauth_packets:
        all_data.extend(deauth_packets)
    if rf_jam:
        all_data.append(rf_jam)

    # Check for alerts
    total_devices = len(all_data)
    if config.ALERT_ON_BURST and total_devices > config.BURST_THRESHOLD:
        logger.warning(f"Burst traffic detected: {total_devices} devices")
    if config.ALERT_ON_LOW_TRAFFIC and total_devices < config.LOW_TRAFFIC_THRESHOLD:
        logger.warning(f"Low traffic detected: {total_devices} devices")

    # Add metadata to each entry
    for d in all_data:
        d.update({
            "timestamp": timestamp,
            "sensor": config.SENSOR_ID,
            **gps
        })

    # Send data if available
    if all_data:
        try:
            response = requests.post(
                config.WEBHOOK_URL,
                json=all_data,
                headers=config.HEADERS,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Successfully sent {len(all_data)} records")
        except requests.RequestException as e:
            logger.error(f"Failed to send data: {e}")

if __name__ == "__main__":
    asyncio.run(main())