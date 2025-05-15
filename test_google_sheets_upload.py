# test_google_sheets_upload.py
# Verifies upload to Google Sheets using service account

from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

CREDENTIALS = "credentials.json"
SPREADSHEET_ID = os.getenv("GSHEET_ID", None)

if not SPREADSHEET_ID:
    raise Exception("GSHEET_ID environment variable not set.")

credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
service = build("sheets", "v4", credentials=credentials)

sheet = service.spreadsheets()
body = {
    "values": [
        ["Timestamp", "MAC Hash", "RSSI", "Sensor"],
        ["1715712345", "hashvalue123", "-55", "TestSensor"]
    ]
}
sheet.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range="Sheet1!A1",
    valueInputOption="RAW",
    body=body
).execute()
print("Test data uploaded to Google Sheet.")
