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
