import asyncio
from bleak import BleakScanner
import time, hashlib, sqlite3, os, csv
from datetime import datetime, timezone, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

DB = "/opt/ble-logger/ble_logs.db"
LOCATION = os.getenv("SENSOR_ID", "Unknown")
SERVICE_ACCOUNT_FILE = "/opt/ble-logger/credentials.json"
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", None)
SHEET_ID = os.getenv("GSHEET_ID", None)

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scans (
        timestamp INTEGER, mac_hash TEXT, rssi INTEGER, sensor TEXT)''')
    conn.commit()
    conn.close()

async def scan_and_log():
    devices = await BleakScanner.discover(timeout=10.0)
    timestamp = int(time.time())
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for d in devices:
        mac_hash = hashlib.sha256(d.address.encode()).hexdigest()
        c.execute("INSERT INTO scans VALUES (?, ?, ?, ?)",
                  (timestamp, mac_hash, d.rssi, LOCATION))
    conn.commit()
    conn.close()

def export_weekly_csv():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute("SELECT * FROM scans").fetchall()
    conn.close()

    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).date()
    filename = f"/opt/ble-logger/{LOCATION}_{week_start}_ble_logs.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "datetime", "mac_hash", "rssi", "sensor"])
        for row in rows:
            dt = datetime.fromtimestamp(row[0], timezone.utc).isoformat()
            writer.writerow([row[0], dt, row[1], row[2], row[3]])
    return filename

def upload_to_drive(file_path, file_name, mime_type):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build("drive", "v3", credentials=credentials)

    file_metadata = {
        "name": file_name,
        "mimeType": mime_type
    }
    if GDRIVE_FOLDER_ID:
        file_metadata["parents"] = [GDRIVE_FOLDER_ID]

    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    service.files().create(body=file_metadata, media_body=media, fields="id").execute()

def upload_to_google_sheets(rows):
    if not SHEET_ID:
        return
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=credentials)
    sheet = service.spreadsheets()

    values = [["Timestamp", "Datetime", "MAC Hash", "RSSI", "Sensor"]]
    for row in rows:
        dt = datetime.fromtimestamp(row[0], timezone.utc).isoformat()
        values.append([row[0], dt, row[1], row[2], row[3]])

    body = {"values": values}
    try:
        sheet.values().update(
            spreadsheetId=SHEET_ID,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body
        ).execute()
    except HttpError as e:
        print(f"Google Sheets error: {e}")

def clear_logs():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM scans")
    conn.commit()
    conn.close()

# Main execution
init_db()
asyncio.run(scan_and_log())

# After scan, export weekly CSV and upload
conn = sqlite3.connect(DB)
c = conn.cursor()
scan_rows = c.execute("SELECT * FROM scans").fetchall()
conn.close()

csv_file = export_weekly_csv()
upload_to_drive(DB, f"{LOCATION}_ble_logs.db", "application/x-sqlite3")
upload_to_drive(csv_file, os.path.basename(csv_file), "text/csv")
upload_to_google_sheets(scan_rows)
clear_logs()
