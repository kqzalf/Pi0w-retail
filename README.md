# BLE + Wi-Fi + GPS Foot Traffic Logger

pi20w : https://a.co/d/0FehVMd

gps hat: https://a.co/d/dVvAXLA


This project provides a complete solution for anonymously tracking foot traffic in physical spaces using Raspberry Pi Zero W or similar low-power devices. It detects nearby Bluetooth Low Energy (BLE) and Wi-Fi devices, hashes their MAC addresses for anonymity, optionally tags GPS coordinates, and uploads the data to a webhook endpoint for real-time alerting, analytics, and dashboarding.

---

## 🚀 Features

| Feature                     | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| BLE + Wi-Fi Scanning       | Passive scanning for all nearby broadcasting BLE and Wi-Fi devices         |
| MAC Hashing                | SHA-256 anonymization of detected device MACs                               |
| GPS Tagging                | Optional support for GPS coordinates (via USB or GPIO GPS modules)          |
| n8n Integration            | Fully compatible with n8n for logging, alerts, dashboards                   |
| Google Sheets Logging      | Log all data to Google Sheets via n8n                                        |
| Slack Alerts               | Real-time alerts for burst traffic, low/no traffic, and repeat visitors     |
| Looker Studio Dashboard    | Connect Google Sheets to visualize historical data                          |
| Systemd Service            | Logger auto-starts and runs in background on boot                           |
| Heatmap Generator          | Generates HTML heatmaps of device density                                   |
| Scheduled Heatmaps         | Cron integration to auto-generate new heatmaps (every 6 hours, by default) |
| Full Provisioning Script   | Automatically sets up the Pi with all software and system configs           |
| Git Auto-Update            | Sensors can pull latest repo updates on boot                                |
| ENV-Based Sensor ID        | Auto-name devices and inject into log stream via environment variable       |

---

## 🧰 Hardware Requirements

- Raspberry Pi Zero W or Zero 2 W
- MicroSD card (8GB+)
- BLE + Wi-Fi antenna (internal OK)
- Optional: GPS module (UART or USB)
- Power supply
- Internet access (via Wi-Fi)

---

## 🛠 Pi Headless Setup

### 1. Flash Raspberry Pi OS Lite
Use Raspberry Pi Imager or BalenaEtcher.

### 2. Configure `/boot` Partition
Add these files to enable headless Wi-Fi + SSH:
- `wpa_supplicant.conf` (included)
- An empty file named `ssh`

---

## ⚙️ First-Time Provisioning (One Command Setup)

SSH into the Pi after first boot and run:

```bash
chmod +x provision_pi.sh
SENSOR_ID=pi-west TIMEZONE=America/Chicago ./provision_pi.sh
```

This script:
- Updates the system
- Installs all Python packages
- Pulls the latest repo (or updates it)
- Registers the systemd service
- Injects your `SENSOR_ID` into the logger
- Sets hostname and timezone

---

## 🖥 Running the Logger

The systemd service runs the logger every minute on boot:
```bash
sudo systemctl status ble-logger.service
sudo journalctl -u ble-logger.service -f
```

Manually test the script:
```bash
python3 ble_wifi_gps_logger_pi.py
```

---

## 📡 Data Format Example

```json
[
  {
    "mac_hash": "e3f0...d1ac",
    "rssi": -71,
    "type": "ble",
    "timestamp": 1713123849,
    "sensor": "pi-west",
    "lat": 38.974,
    "lon": -94.595
  }
]
```

---

## 🗺️ Heatmap Generation

### Manual
```bash
python3 generate_heatmap.py
```

### Scheduled
Add to crontab:
```bash
crontab -e
# Every 6 hours:
0 */6 * * * /home/pi/ble-foot-traffic-logger/schedule_heatmap.sh
```

HTML heatmaps are saved with timestamped filenames.

---

## 📊 Dashboard with Looker Studio

1. Connect your Google Sheet to Looker Studio
2. Use provided metrics:
   - Daily device count
   - Per-sensor scan volumes
   - Geo heatmaps (if GPS-enabled)
3. Import dashboard template from `looker_dashboard_template.json`

---

## 🔔 Alerting System via n8n

| Trigger                    | Description                          |
|----------------------------|--------------------------------------|
| Repeat Visitor             | Same `mac_hash` seen multiple times |
| MAC Burst                  | >10 devices in a single scan         |
| Low Traffic                | <2 devices seen                     |
| GPS Drift (optional)       | Sensor outside expected range       |
| Sensor Offline (external)  | Heartbeat timeout monitoring        |

All alerts are sent via Slack, configurable in `n8n-ble-workflow.json`.

---

## 🧪 CI: Linting with GitHub Actions

Included `.pylintrc` and `.github/workflows/lint.yml` allow for auto-linting on every push.

---

## 📦 Installation Summary

```bash
git clone https://github.com/your-org/ble-foot-traffic-logger.git
cd ble-foot-traffic-logger
pip install -r requirements.txt
python3 ble_wifi_gps_logger_pi.py
```

---

## 📁 Directory Overview

| File/Folder                | Description                              |
|---------------------------|------------------------------------------|
| `ble_wifi_gps_logger_pi.py` | Main sensor scanner script              |
| `generate_heatmap.py`     | Script to generate heatmaps               |
| `provision_pi.sh`         | One-command setup script for the Pi       |
| `schedule_heatmap.sh`     | Cron-compatible wrapper for heatmaps      |
| `ble_logger.service`      | Systemd unit definition                   |
| `requirements.txt`        | Python dependencies                       |
| `n8n-ble-workflow.json`   | Example n8n integration workflow          |
| `README.md`               | You're reading it.                        |

---

## 📝 License

MIT License — free to use and adapt with attribution.
