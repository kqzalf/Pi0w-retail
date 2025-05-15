# Pi0w-retail

This project provides a complete solution for anonymously tracking foot traffic in physical spaces using Raspberry Pi Zero W or similar low-power devices. It detects nearby Bluetooth Low Energy (BLE) and Wi-Fi devices, hashes their MAC addresses for anonymity, optionally tags GPS coordinates, and uploads the data to a webhook endpoint for real-time alerting, analytics, and dashboarding.

## 🚀 Features

| Feature                      | Description                                                                  |
|------------------------------|------------------------------------------------------------------------------|
| BLE + Wi-Fi Scanning         | Passive scanning for all nearby broadcasting BLE and Wi-Fi devices          |
| Wi-Fi Deauthentication Detection | Detects Wi-Fi deauthentication attacks and logs MAC addresses (unencrypted) |
| RF Jamming Detection         | Identifies RF jamming attempts based on signal-to-noise ratio (SNR) analysis |
| MAC Hashing                  | SHA-256 anonymization of detected device MACs                                |
| GPS Tagging                  | Optional support for GPS coordinates (via USB or GPIO GPS modules)           |
| n8n Integration              | Fully compatible with n8n for logging, alerts, dashboards                    |
| Google Sheets Logging        | Log all data to Google Sheets via n8n                                        |
| Slack Alerts                 | Real-time alerts for burst traffic, low/no traffic, and repeat visitors      |
| Looker Studio Dashboard      | Connect Google Sheets to visualize historical data                           |
| Systemd Service              | Logger auto-starts and runs in background on boot                            |
| Heatmap Generator            | Generates HTML heatmaps of device density                                    |
| Scheduled Heatmaps           | Cron integration to auto-generate new heatmaps (every 6 hours, by default)   |
| Full Provisioning Script     | Automatically sets up the Pi with all software and system configs            |
| Git Auto-Update              | Sensors can pull latest repo updates on boot                                 |
| ENV-Based Sensor ID          | Auto-name devices and inject into log stream via environment variable        |

---

## 🛠️ Hardware Requirements

- Raspberry Pi Zero W or Zero 2 W
- MicroSD card (8GB+)
- BLE + Wi-Fi antenna (internal OK)
- Optional: GPS module (UART or USB)
- Power supply
- Internet access (via Wi-Fi)

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

## 🖥️ Running the Logger

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

## 📄 Data Format Example

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
  },
  {
    "type": "deauth",
    "mac": "00:11:22:33:44:55",
    "timestamp": 1713123849,
    "sensor": "pi-west",
    "lat": 38.974,
    "lon": -94.595
  },
  {
    "type": "rf_jamming",
    "avg_noise": -95,
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
| MAC Burst                  | >10 devices in a single scan        |
| Low Traffic                | <2 devices seen                     |
| GPS Drift (optional)       | Sensor outside expected range       |
| Sensor Offline (external)  | Heartbeat timeout monitoring        |

All alerts are sent via Slack, configurable in `n8n-ble-workflow.json`.

---

## 🖋️ License

MIT License — free to use and adapt with attribution.