# export_html_to_pdf.py
# Converts a folium heatmap to a timestamped PDF and uploads it to Google Drive

import asyncio
from pyppeteer import launch
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

SERVICE_ACCOUNT_FILE = "credentials.json"
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", None)

async def html_to_pdf_and_upload(input_html):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_pdf = f"ble_heatmap_{timestamp}.pdf"

    # Generate PDF from HTML
    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    await page.goto(f'file://{os.path.abspath(input_html)}', {'waitUntil': 'networkidle0'})
    await page.pdf({
        'path': output_pdf,
        'format': 'A4',
        'printBackground': True
    })
    await browser.close()
    print(f"PDF saved: {output_pdf}")

    # Upload to Google Drive
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build("drive", "v3", credentials=credentials)

    file_metadata = {
        "name": output_pdf,
        "mimeType": "application/pdf"
    }
    if GDRIVE_FOLDER_ID:
        file_metadata["parents"] = [GDRIVE_FOLDER_ID]

    media = MediaFileUpload(output_pdf, mimetype="application/pdf", resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print("Uploaded to Google Drive. File ID:", file.get("id"))

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(
        html_to_pdf_and_upload("ble_heatmap.html")
    )
