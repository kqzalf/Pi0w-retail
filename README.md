# BLE + Wi-Fi + GPS Foot Traffic Logger

This project uses Raspberry Pi Zero W devices to detect nearby BLE and Wi-Fi devices, hash their MAC addresses, and send presence data to a central webhook for processing, alerting, and dashboarding.

## Features

- BLE and Wi-Fi passive scanning
- MAC address anonymization (SHA-256)
- GPS tagging support
- n8n integration with Slack alerts
- Google Drive + Sheets logging
- PDF heatmap generation with blueprint overlay
- Looker Studio dashboard template
- No sensitive credentials on sensor devices

## Setup

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Run Logger on Pi
```bash
python3 ble_wifi_gps_logger_pi.py
```

### Run Heatmap and Export
```bash
python3 generate_heatmap.py
python3 export_html_to_pdf.py
```

### Lint Codebase
```bash
pylint $(git ls-files '*.py')
```

## Alerting (via n8n)

| Alert                     | Description |
|--------------------------|-------------|
| Repeat Visitor           | Same hash detected more than once in session |
| MAC Burst Detection      | Over 10 devices detected in a single scan |
| Low Traffic Detection    | Fewer than 2 devices seen in a scan |
| GPS Drift Detection      | Invalid GPS coordinates from sensor |
| Sensor Offline Detection | (External: monitor missing webhook calls) |

## License

MIT License.


---

## 🧩 Full Feature List

| Feature                       | Description                                                               |
|------------------------------|---------------------------------------------------------------------------|
| BLE + Wi-Fi Scanning         | Detects nearby devices using passive scan (BLE + 2.4GHz Wi-Fi)            |
| MAC Hashing (SHA-256)        | Obfuscates device identity to preserve privacy                            |
| GPS Tagging                  | Adds GPS coordinates if module available                                  |
| n8n Integration              | Sends scan data via webhook to n8n for logging + alerting                 |
| Slack Alerts                 | Real-time alerts for burst traffic, low traffic, repeat visitors          |
| Google Sheets Logging        | Appends every scan row into a structured log sheet                        |
| Heatmap Generator            | Creates Folium HTML heatmaps with device density                         |
| Weekly Heatmap Schedule      | Auto-generates heatmaps via cron                                          |
| Looker Studio Dashboard      | View trends and traffic with connected Google Sheets                      |
| Provisioning Script          | One-command setup on any Pi for sensor deployment                        |
| Systemd Service              | Auto-starts the logger on boot via `ble_logger.service`                  |
| Fleet Sensor ID              | Auto-names sensors using environment variables                            |
| Git Auto-update              | Pulls the latest code from repo during provisioning                       |

---

## 🚀 Deployment: Step-by-Step Instructions

### 🖥 1. Prepare Your Raspberry Pi (Headless)
- Flash Raspberry Pi OS Lite to SD
- Add `wpa_supplicant.conf` to `/boot` for Wi-Fi
- Add an empty `ssh` file to enable SSH

### 🔌 2. First Boot & SSH In
```bash
ssh pi@raspberrypi.local
```

### ⚙️ 3. Provision the Pi
```bash
chmod +x provision_pi.sh
SENSOR_ID=pi-east TIMEZONE=America/Chicago ./provision_pi.sh
```
This will:
- Pull the latest repo
- Install dependencies
- Register the systemd logger
- Insert your sensor ID into the script

### 🧲 4. Enable Heatmap Scheduling (optional)
```bash
crontab -e
# Add this line:
0 */6 * * * /home/pi/ble-foot-traffic-logger/schedule_heatmap.sh
```

### 🌐 5. Deploy n8n Server
Use Docker:
```bash
docker run -it --rm -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
```

Import `n8n-ble-workflow.json`, connect Slack + Google Sheets, and activate the Webhook node.

### 📡 6. Configure Webhook
Edit `ble_wifi_gps_logger_pi.py`:
```python
WEBHOOK_URL = "https://your-server.com/webhook/ble-data"
```

### 🗺 7. View Heatmaps
Heatmaps are saved as `ble_heatmap_<timestamp>.html` in the logger directory.
Open them in your browser.

### 📊 8. Looker Studio Dashboard
- Connect Google Sheet used by n8n
- Use provided metrics to visualize traffic

---

Let me know if you'd like multi-store deployment tips, sensor inventory scripts, or QR-based scanner configs.
