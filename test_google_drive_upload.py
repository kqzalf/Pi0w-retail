# test_google_drive_upload.py
# Uploads a test file to Google Drive using the service account

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CREDENTIALS = "credentials.json"
TEST_FILE = "test_upload.txt"
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", None)

with open(TEST_FILE, "w") as f:
    f.write("This is a test file for Google Drive upload.")

credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS, scopes=["https://www.googleapis.com/auth/drive.file"]
)
service = build("drive", "v3", credentials=credentials)

file_metadata = {
    "name": "test_upload.txt",
    "mimeType": "text/plain"
}
if GDRIVE_FOLDER_ID:
    file_metadata["parents"] = [GDRIVE_FOLDER_ID]

media = MediaFileUpload(TEST_FILE, mimetype="text/plain", resumable=True)
file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
print("Uploaded file ID:", file.get("id"))
