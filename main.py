import os
from dotenv import load_dotenv
from utils.logger import logger
from services.google_services import (
    load_service_account_credentials,
    list_files_in_drive,
    append_to_google_sheets,
)
from services.llm_processor import process_text_with_llm
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()


def main():
    try:
        # Get variables from .env file
        SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
        SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
        FOLDER_ID = os.getenv("FOLDER_ID")

        if not SERVICE_ACCOUNT_FILE or not SPREADSHEET_ID or not FOLDER_ID:
            logger.error(
                "One or more environment variables are missing. Please check the .env file."
            )
            return

        # Define the required scopes
        SCOPES = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ]

        # Load credentials and create service objects
        credentials = load_service_account_credentials(SERVICE_ACCOUNT_FILE, SCOPES)
        drive_service = build("drive", "v3", credentials=credentials)
        sheets_service = build("sheets", "v4", credentials=credentials)

        # List files in Google Drive, download PDFs, and extract text
        file_data = list_files_in_drive(drive_service, FOLDER_ID)

        # Process each extracted text to identify relevant columns
        for file_name, extracted_text in file_data:
            extracted_columns = process_text_with_llm(extracted_text)

            # Append the processed data to the respective Google Sheets
            for sheet_name, columns in extracted_columns.items():
                RANGE_NAME = f"{sheet_name}!A1"  # Adjust the range as necessary
                append_to_google_sheets(
                    sheets_service, SPREADSHEET_ID, RANGE_NAME, columns
                )

    except Exception as e:
        logger.critical(f"An unexpected error occurred in the main function: {e}")


if __name__ == "__main__":
    main()
