import os
from dotenv import load_dotenv
from utils.logger import logger
from services.google_services import (
    load_service_account_credentials,
    list_files_in_drive,
    append_to_google_sheets,
    watch_drive_folder,  # New function to watch a Drive folder
    handle_file_upload,  # New function to handle the uploaded file
)
from fastapi import FastAPI, Request, HTTPException
from googleapiclient.discovery import build

import uvicorn

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
FOLDER_ID = os.getenv("FOLDER_ID")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

credentials = load_service_account_credentials(SERVICE_ACCOUNT_FILE, SCOPES)
drive_service = build("drive", "v3", credentials=credentials)
sheets_service = build("sheets", "v4", credentials=credentials)


@app.post("/webhook")
async def drive_webhook(request: Request):
    """Endpoint to receive Google Drive notifications."""
    try:
        data = await request.json()
        logger.info(f"Received notification: {data}")

        # Example: Check for the correct folder or event type
        if "fileId" in data:
            handle_file_upload(drive_service, sheets_service, data["fileId"])

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def main():
    try:
        if not SERVICE_ACCOUNT_FILE or not SPREADSHEET_ID or not FOLDER_ID:
            logger.error(
                "One or more environment variables are missing. Please check the .env file."
            )
            return

        # Watch the folder for changes
        watch_drive_folder(drive_service, FOLDER_ID)

        # Start the FastAPI app (webhook listener)
        uvicorn.run(app, host="0.0.0.0", port=5000)

    except Exception as e:
        logger.critical(f"An unexpected error occurred in the main function: {e}")


if __name__ == "__main__":
    main()
