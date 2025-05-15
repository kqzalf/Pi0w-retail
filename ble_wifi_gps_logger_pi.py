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
from scapy.all import sniff, Dot11  # pylint: disable=import-error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class HardwareConfig:
    """Hardware-related configuration settings."""
    gps_port: str = os.getenv('GPS_PORT', '/dev/ttyAMA0')
    gps_baudrate: int = int(os.getenv('GPS_BAUDRATE', '9600'))
    wifi_interface: str = os.getenv('WIFI_INTERFACE', 'wlan0')
    wifi_monitor_interface: str = os.getenv('WIFI_MONITOR_INTERFACE', 'wlan0mon')

@dataclass
class AlertConfig:
    """Alert-related configuration settings."""
    rf_jamming_threshold: int = int(os.getenv('RF_JAMMING_THRESHOLD', '-90'))
    burst_threshold: int = int(os.getenv('BURST_THRESHOLD', '10'))
    low_traffic_threshold: int = int(os.getenv('LOW_TRAFFIC_THRESHOLD', '2'))
    gps_drift_threshold: float = float(os.getenv('GPS_DRIFT_THRESHOLD', '0.001'))
    alert_on_burst: bool = os.getenv('ALERT_ON_BURST', 'true').lower() == 'true'
    alert_on_low_traffic: bool = os.getenv('ALERT_ON_LOW_TRAFFIC', 'true').lower() == 'true'
    alert_on_gps_drift: bool = os.getenv('ALERT_ON_GPS_DRIFT', 'true').lower() == 'true'

@dataclass
class Config:
    """Configuration settings for the sensor."""
    sensor_id: str = os.getenv('SENSOR_ID', 'HybridPi')
    webhook_url: str = os.getenv('WEBHOOK_URL', 'https://your-n8n-server.com/webhook/ble-data')
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    scan_timeout: int = int(os.getenv('SCAN_TIMEOUT', '10'))
    gps_enabled: bool = os.getenv('GPS_ENABLED', 'true').lower() == 'true'
    hardware: HardwareConfig = HardwareConfig()
    alerts: AlertConfig = AlertConfig()

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
            ["sudo", "iw", "dev", config.hardware.wifi_interface, "scan"],
            text=True,
            timeout=config.scan_timeout
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
                    logger.warning("Failed to parse signal strength: %s", e)
                    continue
        if mac:
            seen.append({"mac_hash": sha256(mac), "rssi": signal, "type": "wifi"})
        return seen
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error("Wi-Fi scan failed: %s", e)
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
            logger.warning("[Deauth Detected] MAC: %s", mac_address)
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
            iface=config.hardware.wifi_monitor_interface,
            prn=detect_deauth,
            store=0,
            timeout=config.scan_timeout
        )
    except (IOError, OSError) as e:
        logger.error("Failed to monitor Wi-Fi deauth: %s", e)
        return []

def detect_rf_jamming() -> Optional[Dict[str, Union[str, float]]]:
    """Detect RF jamming by analyzing noise levels.
    
    Returns:
        Dictionary containing jamming information if detected, None otherwise
    """
    try:
        output = subprocess.check_output(
            ["iw", "dev", config.hardware.wifi_interface, "station", "dump"],
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
        if avg_noise < config.alerts.rf_jamming_threshold:
            logger.warning("[RF Jamming Detected]")
            return {"type": "rf_jamming", "avg_noise": avg_noise}
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error("RF jamming detection failed: %s", e)
    return None

def get_gps() -> Dict[str, float]:
    """Read GPS coordinates if GPS hardware is present.
    
    Returns:
        Dictionary containing latitude and longitude if available
    """
    try:
        with serial.Serial(
            config.hardware.gps_port,
            config.hardware.gps_baudrate,
            timeout=1
        ) as ser:
            for _ in range(10):  # Try up to 10 times
                line = ser.readline().decode("ascii", errors="replace")
                if line.startswith("$GPGGA"):
                    msg = pynmea2.parse(line)
                    return {"lat": msg.latitude, "lon": msg.longitude}
    except (serial.SerialException, pynmea2.ParseError) as e:
        logger.error("GPS reading failed: %s", e)
    return {}

async def scan_ble() -> List[Dict[str, Union[str, int]]]:
    """Scan BLE devices and hash their MACs.
    
    Returns:
        List of dictionaries containing hashed MAC addresses, RSSI values, and device type
    """
    try:
        devices = await BleakScanner.discover(timeout=config.scan_timeout)
        return [
            {
                "mac_hash": sha256(d.address),
                "rssi": d.rssi,
                "type": "ble"
            }
            for d in devices
        ]
    except (BleakError, ValueError) as e:
        logger.error("BLE scan failed: %s", e)
        return []

async def main() -> None:
    """Main logic to scan, tag, and send all signals."""
    timestamp = int(time.time())

    # Gather all data
    ble = await scan_ble()
    wifi = get_wifi_devices()
    gps = get_gps() if config.gps_enabled else {}
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
    if config.alerts.alert_on_burst and total_devices > config.alerts.burst_threshold:
        logger.warning("Burst traffic detected: %d devices", total_devices)
    if config.alerts.alert_on_low_traffic and total_devices < config.alerts.low_traffic_threshold:
        logger.warning("Low traffic detected: %d devices", total_devices)

    # Add metadata to each entry
    for d in all_data:
        d.update({
            "timestamp": timestamp,
            "sensor": config.sensor_id,
            **gps
        })

    # Send data if available
    if all_data:
        try:
            response = requests.post(
                config.webhook_url,
                json=all_data,
                headers=config.headers,
                timeout=5
            )
            response.raise_for_status()
            logger.info("Successfully sent %d records", len(all_data))
        except requests.RequestException as e:
            logger.error("Failed to send data: %s", e)

if __name__ == "__main__":
    asyncio.run(main()) 
 