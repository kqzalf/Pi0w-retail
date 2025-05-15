# BLE Foot Traffic Logger (Secure & Scalable)

This project uses Raspberry Pi Zero W devices to detect Bluetooth presence anonymously and send that data securely to a central server. The server aggregates logs, generates weekly heatmaps, and uploads them to Google Drive and Google Sheets — without storing any sensitive credentials on edge devices.

---

## Features

- 📡 BLE scanning with hashed MACs (privacy-safe)
- 🔐 No Google credentials stored on the Pi
- 🧠 Central server processes data, exports PDFs, and uploads to Google Drive/Sheets
- 🗺️ Weekly heatmap generation with floor plan overlays
- 🧪 Test harnesses for BLE, Drive, Sheets, and heatmap PDF generation
- 📦 Docker-compatible and Pi-ready

---

## Architecture Overview

### Raspberry Pi Zero W (BLE Sensor)
- Performs BLE scans with `bleak`
- Hashes MACs and timestamps locally
- Sends data via HTTPS `POST` to the central server
- Does not store data or credentials locally

### Central Server (Secure Cloud/VPS/Local)
- Receives BLE scan data via Flask API
- Logs data to SQLite/Postgres
- Exports weekly CSV files
- Renders HTML heatmaps with store blueprint overlays
- Converts heatmaps to timestamped PDFs
- Uploads files to Google Drive and updates Google Sheets

---

## Requirements

### On Pi Zero W:
- Python 3
- `bleak`, `requests`
- Wi-Fi access and HTTPS capability

### On Server:
- Python 3
- `flask`, `pandas`, `folium`, `pyppeteer`
- Google API service account (`credentials.json`)
- Docker (optional)

---

## Repository Structure

```
ble-foot-traffic-logger/
├── ble_logger_pi.py             # Minimal sensor-side BLE scan + exfil script
├── server/
│   ├── app.py                   # Flask API to receive and log scan data
│   ├── generate_heatmap.py      # Weekly heatmap + floor plan overlay
│   ├── export_html_to_pdf.py    # Converts HTML heatmap to timestamped PDF + uploads
│   └── utils.py                 # Common data helpers (optional)
├── store_blueprint.png          # Your store layout image (JPG/PNG)
├── wpa_supplicant.conf          # Headless Pi Wi-Fi config
├── pi0w-setup.sh                # Pi bootstrap script
├── docker-compose.yml           # Server-side stack
├── README.md
```

---

## Headless Pi Setup

1. Flash Raspberry Pi OS Lite to SD
2. Add empty `ssh` file to `/boot`
3. Add `wpa_supplicant.conf` with your Wi-Fi credentials
4. SSH into Pi and run:
```bash
sudo apt update && sudo apt install -y python3-pip
pip3 install bleak requests
```

5. Run BLE sensor script:
```bash
python3 ble_logger_pi.py
```

---

## Central Server Setup

1. Install Python dependencies:
```bash
pip install flask pandas folium pyppeteer google-api-python-client google-auth
```

2. Place your `credentials.json` file in `server/`

3. Set environment variables:
```bash
export GDRIVE_FOLDER_ID="your_drive_folder_id"
export GSHEET_ID="your_google_sheet_id"
```

4. Start Flask server:
```bash
cd server
python3 app.py
```

5. Set up a cron job to:
- Run `generate_heatmap.py`
- Run `export_html_to_pdf.py`

---

## Google Cloud Setup

1. Enable Google Drive API & Google Sheets API
2. Create a service account and download `credentials.json`
3. Share target Google Sheet and Drive folder with the service account's email

---

## File Outputs

- `ble_logs.db` → all scans stored on the server
- `ble_heatmap_<timestamp>.html` → interactive map
- `ble_heatmap_<timestamp>.pdf` → exported and uploaded to Drive
- Google Sheet is updated with latest logs

---

## Security Best Practices

- No credentials on Pi devices
- HTTPS POST with authentication (API keys or JWTs)
- Compressed payloads (optional)
- Timestamped logs + central auditing

---

## Next Steps

- [ ] Enable sensor authentication (JWT or tokens)
- [ ] Add email reports or Slack notifications
- [ ] Support for Wi-Fi presence detection
- [ ] Google Looker Studio dashboard

---

## License

MIT License

---

## 📡 Wi-Fi Presence Detection

This repository supports passive Wi-Fi presence detection in addition to BLE scanning.

Using `iw dev wlan0 scan`, nearby access points and their signal strength (RSSI) are collected, anonymized (MAC hashed), and sent along with BLE and optional GPS data.

To use this feature, run the hybrid logger script:
```bash
python3 ble_wifi_gps_logger_pi.py
```

It will scan for:
- BLE devices (via `bleak`)
- Wi-Fi APs (via `iw scan`)
- GPS data (if attached)

Each record will include:
- `timestamp`
- `mac_hash`
- `rssi`
- `sensor`
- Optional `lat` / `lon`
- `type`: `ble` or `wifi`

---

## 📊 Google Looker Studio Dashboard (Template)

You can visualize foot traffic by importing your Google Sheets data or BigQuery table into Google Looker Studio.

Suggested metrics:
- Daily traffic volume per sensor
- RSSI trends over time
- Top repeat device hashes
- Heatmap by zone or GPS cluster

🔗 **Template Link:** *(Insert your own link after publishing)*

To build your own dashboard:
1. Open [Looker Studio](https://lookerstudio.google.com/)
2. Click “Blank Report”
3. Connect to:
   - Google Sheets: Select the sheet updated by n8n
   - Or BigQuery: Use data piped from your backend DB
4. Use filters on `sensor`, date range, and device count

Let me know if you’d like a custom Looker Studio JSON to import directly.


---

## 🔔 Alerting System

This repository includes a powerful n8n-based alerting pipeline triggered by BLE/Wi-Fi/GPS scans.

### Real-Time Alerts Sent to Slack

| Alert Type            | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| 👤 Repeat Visitor     | MAC hash seen again in the same session                                     |
| 📈 MAC Burst          | 10+ new devices seen in one scan                                            |
| 📉 Low Traffic        | Less than 2 devices seen per scan                                           |
| 🧭 GPS Drift          | GPS coordinate anomaly (e.g., invalid latitude)                             |
| 🚨 Sensor Offline     | *(expected to be handled externally by heartbeat monitor or timeout trigger)*

You can view or extend alerting in the provided n8n workflow:
- File: `n8n-ble-workflow.json`
- Slack credentials must be configured in n8n’s credential manager

To use the enhanced workflow:
1. Import `n8n-ble-workflow.json` into your n8n instance
2. Configure Slack and Google Sheets credentials
3. Activate the Webhook node to start receiving BLE data

You may modify threshold values, routes, or escalate alerts via:
- Email
- PagerDuty
- Microsoft Teams
- SMS (via Twilio or other)

