from flask import Flask, request
import threading
import json
import os
from googleapiclient.discovery import build
from services.google_services import (
    load_service_account_credentials,
    download_pdf_from_drive,
)
from main import process_file  # Import your file processing function
from utils.logger import logger

app = Flask(__name__)

# Load environment variables
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
FOLDER_ID = os.getenv("FOLDER_ID")
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Initialize credentials and services
credentials = load_service_account_credentials(SERVICE_ACCOUNT_FILE, SCOPES)
drive_service = build("drive", "v3", credentials=credentials)
sheets_service = build("sheets", "v4", credentials=credentials)


def save_start_page_token(token):
    with open("start_page_token.txt", "w") as f:
        f.write(token)


def load_start_page_token():
    if os.path.exists("start_page_token.txt"):
        with open("start_page_token.txt", "r") as f:
            return f.read()
    return None


@app.route("/webhook", methods=["POST"])
def webhook():
    # Parse the notification
    channel_id = request.headers.get("X-Goog-Channel-ID")
    resource_state = request.headers.get("X-Goog-Resource-State")

    logger.info(
        f"Received notification: Channel ID {channel_id}, Resource State {resource_state}"
    )

    if resource_state == "sync":
        logger.info("Sync notification received.")
        return "", 200

    # Handle the notification in a separate thread
    threading.Thread(target=handle_change).start()

    return "", 200


sheet_headers = {
    "Leadership": [
        "Deal_ID",
        "Name",
        "Title",
        "Description",
        "Years_in_Industry",
        "Sponsor_Name_Rank",
    ],
    "Compensation": [
        "Deal_ID",
        "Type_of_Payment",
        "Determination_of_Amount",
        "Estimated_Amount",
        "Sponsor_Compensation_Rank",
    ],
    "Track Record": [
        "Program_Name",
        "PPM_Projected_Cash_on_Cash_Return_2023",
        "Avg_Cash_on_Cash_Return_from_Inception_through_12/31/2023",
        "Property_Type",
        "Deal_ID",
        "Sponsor_Record_Rank",
    ],
    "Use of Proceeds": [
        "Deal_ID",
        "Loan_Proceeds",
        "Loan_Proceeds_%",
        "Equity_Proceeds",
        "Equity_Proceeds_%",
        "Selling_Commissions",
        "Selling_Commissions_%",
        "Property_Purchase_Price",
        "Property_Purchase_Price_%",
        "Trust_Held_Reserve",
        "Trust_Held_Reserve_%",
        "Acquisition_Fees",
        "Acquisition_Fees_%",
        "Bridge_Costs",
        "Bridge_Costs_%",
        "Total",
        "LTV_%",
        "Syndication_Load_%",
    ],
    # We'll generate headers for "Projected Results" and "Final Data Table" dynamically
}


def handle_change():
    # Load the saved start page token
    saved_start_page_token = load_start_page_token()

    # Fetch changes since the last saved token
    page_token = saved_start_page_token
    while page_token is not None:
        response = (
            drive_service.changes()
            .list(
                pageToken=page_token,
                spaces="drive",
                fields="nextPageToken,newStartPageToken,changes(fileId,file(name,parents,mimeType))",
            )
            .execute()
        )

        for change in response.get("changes"):
            file = change.get("file")
            if file and file.get("mimeType") == "application/pdf":
                parents = file.get("parents", [])
                if FOLDER_ID in parents:
                    file_id = file.get("id")
                    file_name = file.get("name")
                    logger.info(f"Processing new file: {file_name} ({file_id})")

                    # Download and process the new file
                    file_path = download_pdf_from_drive(
                        drive_service, file_id, file_name
                    )
                    if file_path:
                        process_file(
                            file_name,
                            file_path,
                            sheets_service=sheets_service,
                            SPREADSHEET_ID=SPREADSHEET_ID,
                            sheet_headers=sheet_headers,
                        )

        page_token = response.get("nextPageToken")
        if not page_token:
            # Save the new start page token
            new_start_page_token = response.get("newStartPageToken")
            if new_start_page_token:
                save_start_page_token(new_start_page_token)
            break


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
