# Pi0w-retail

This project provides a complete solution for anonymously tracking foot traffic in physical spaces using Raspberry Pi Zero W or similar low-power devices. It detects nearby Bluetooth Low Energy (BLE) and Wi-Fi devices, hashes their MAC addresses for anonymity, optionally tags GPS coordinates and scans the enviroment for deauthenticatiin attacks and rf jamming, and uploads the data to a webhook endpoint for real-time alerting, analytics, and dashboarding.

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
| ENV-Based Configuration      | Flexible configuration via environment variables                             |

## ⚙️ Configuration

### Environment Variables

| Variable                    | Description                                | Default Value           |
|----------------------------|--------------------------------------------|------------------------|
| SENSOR_ID                  | Unique identifier for the sensor           | HybridPi               |
| WEBHOOK_URL                | n8n webhook endpoint                      | https://your-n8n-server.com/webhook/ble-data |
| GPS_ENABLED               | Enable/disable GPS functionality          | true                   |
| GPS_PORT                  | GPS device port                          | /dev/ttyAMA0          |
| GPS_BAUDRATE             | GPS device baud rate                     | 9600                  |
| WIFI_INTERFACE           | Wi-Fi interface name                     | wlan0                 |
| WIFI_MONITOR_INTERFACE   | Wi-Fi monitor interface name             | wlan0mon              |
| RF_JAMMING_THRESHOLD    | Threshold for RF jamming detection       | -90                   |
| SCAN_TIMEOUT            | Timeout for device scanning (seconds)    | 10                    |
| BURST_THRESHOLD        | Alert threshold for burst traffic        | 10                    |
| LOW_TRAFFIC_THRESHOLD  | Alert threshold for low traffic          | 2                     |
| GPS_DRIFT_THRESHOLD    | Threshold for GPS drift detection        | 0.001                 |

### Heatmap Configuration

| Variable                    | Description                                | Default Value           |
|----------------------------|--------------------------------------------|------------------------|
| HEATMAP_DB_PATH           | Path to the CSV data file                 | ble_logs.csv          |
| HEATMAP_OUTPUT_DIR        | Directory for generated heatmaps          | .                     |
| HEATMAP_RADIUS           | Radius of heatmap points                  | 15                    |
| HEATMAP_BLUR             | Blur factor for heatmap                   | 10                    |
| HEATMAP_MAX_ZOOM         | Maximum zoom level for heatmap            | 1                     |
| MAP_ZOOM_START           | Initial zoom level for map                | 18                    |
| MAP_TILES                | Map tile provider                         | OpenStreetMap         |

## 🛠️ Hardware Requirements

- Raspberry Pi Zero W or Zero 2 W
- MicroSD card (8GB+)
- BLE + Wi-Fi antenna (internal OK)
- Optional: GPS module (UART or USB)
- Power supply
- Internet access (via Wi-Fi)

## 🛍️ Recommended Hardware (Order from Amazon)

Here is a list of recommended hardware that can be ordered from Amazon to set up your Pi0w-retail project:

1. **Raspberry Pi Zero W or Zero 2 W**  
   - [Buy on Amazon](https://a.co/d/0FehVMd)

2. **MicroSD Card (32GB or higher)**  
   - [SanDisk Ultra 32GB MicroSD Card](https://www.amazon.com/dp/B073JWXGNT)

3. **BLE + Wi-Fi Antenna (Optional, for better range)**  
   - [Wi-Fi & BLE Antenna Kit](https://www.amazon.com/dp/B07Y2Z5MVS)

4. **GPS Module (UART or USB)**  
   - [Waveshare L76X GPS Hat for Raspberry Pi](https://www.waveshare.com/l76x-gps-hat.htm)

5. **5V 2.5A Power Supply for Raspberry Pi**  
   - [Official Raspberry Pi Power Supply](https://www.amazon.com/dp/B07TYQRXTK)

6. **Raspberry Pi Case**  
   - [Raspberry Pi Zero W Case (with Heat Sink)](https://www.amazon.com/dp/B07XH1KZNQ)

7. **USB to Micro-USB OTG Adapter**  
   - [Micro-USB OTG Adapter](https://www.amazon.com/dp/B07F6Q48ZP)

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

## 🖥️ Running the Logger

### Systemd Service
The systemd service runs the logger every minute on boot:
```bash
# Check service status
sudo systemctl status ble-logger.service

# View logs
sudo journalctl -u ble-logger.service -f

# Start service
sudo systemctl start ble-logger.service

# Enable service on boot
sudo systemctl enable ble-logger.service
```

### Manual Testing
Test the script manually:
```bash
# Basic test
python3 ble_wifi_gps_logger_pi.py

# Test with custom configuration
SENSOR_ID=test-sensor GPS_ENABLED=true python3 ble_wifi_gps_logger_pi.py
```

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

## 🗺️ Heatmap Generation

### Manual Generation
```bash
# Basic generation
python3 generate_heatmap.py

# Custom configuration
HEATMAP_OUTPUT_DIR=/path/to/output MAP_ZOOM_START=15 python3 generate_heatmap.py
```

### Scheduled Generation
Add to crontab:
```bash
crontab -e

# Every 6 hours:
0 */6 * * * /home/pi/ble-foot-traffic-logger/schedule_heatmap.sh
```

HTML heatmaps are saved with timestamped filenames in the configured output directory.

## 📊 Dashboard with Looker Studio

1. Connect your Google Sheet to Looker Studio
2. Use provided metrics:
   - Daily device count
   - Per-sensor scan volumes
   - Geo heatmaps (if GPS-enabled)
3. Import dashboard template from `looker_dashboard_template.json`

## 🔔 Alerting System via n8n

| Trigger                    | Description                          | Threshold (Configurable) |
|----------------------------|--------------------------------------|-------------------------|
| Repeat Visitor             | Same `mac_hash` seen multiple times | Configurable in n8n     |
| MAC Burst                  | >10 devices in a single scan        | BURST_THRESHOLD        |
| Low Traffic                | <2 devices seen                     | LOW_TRAFFIC_THRESHOLD  |
| GPS Drift                  | Sensor outside expected range       | GPS_DRIFT_THRESHOLD    |
| Sensor Offline             | Heartbeat timeout monitoring        | Configurable in n8n     |

All alerts are sent via Slack, configurable in `n8n-ble-workflow.json`.

## 🔧 Troubleshooting

### Common Issues

1. **GPS Not Working**
   - Check GPS_ENABLED environment variable
   - Verify GPS module connection
   - Check GPS_PORT and GPS_BAUDRATE settings

2. **Wi-Fi Scanning Issues**
   - Ensure monitor mode is enabled
   - Check WIFI_INTERFACE and WIFI_MONITOR_INTERFACE settings
   - Verify sudo permissions

3. **BLE Scanning Issues**
   - Check Bluetooth service status
   - Verify BLE hardware compatibility
   - Check system permissions

4. **Data Not Sending**
   - Verify WEBHOOK_URL is correct
   - Check network connectivity
   - Verify n8n server is running

### Logs and Debugging

- System logs: `sudo journalctl -u ble-logger.service -f`
- Application logs: Check the configured logging output
- Debug mode: Set `LOG_LEVEL=DEBUG` environment variable

## 🔄 Updates and Maintenance

### Git Auto-Update
The system can automatically update on boot:
```bash
# Enable auto-update
sudo systemctl enable git-update.service

# Check update status
sudo systemctl status git-update.service
```

### Manual Update
```bash
git pull origin main
sudo systemctl restart ble-logger.service
```

## 🖋️ License

MIT License — free to use and adapt with attribution.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 Changelog

### v1.1.0
- Added environment variable configuration
- Improved error handling and logging
- Enhanced heatmap generation
- Added data validation
- Added GPS drift detection

### v1.0.0
- Initial release