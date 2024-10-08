import os
from dotenv import load_dotenv
from services.file_processor import process_file
from utils.logger import logger
from services.google_services import (
    load_service_account_credentials,
    list_files_in_drive,
)
from googleapiclient.discovery import build
from utils.common import (
    load_processed_file_ids,
    save_processed_file_ids,
    sheet_headers,
)

# Load environment variables from .env file
load_dotenv()

DEAL_ID = os.getenv("DEAL_ID")  # The Deal ID to use during processing


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

        # List and process the latest file
        processed_file_ids = load_processed_file_ids("processed_files.txt")

        while True:
            logger.info("Checking for new files in Google Drive folder...")
            # List files in the specified folder
            files = list_files_in_drive(drive_service, FOLDER_ID)

            # 'files' is a list of tuples: (file_id, file_name, file_path)
            for file_id, file_name, file_path in files:
                if file_id not in processed_file_ids:
                    logger.info(f"Processing new file: {file_name}")
                    # Process the PDF file
                    process_file(
                        file_name,
                        file_path,
                        sheets_service,
                        SPREADSHEET_ID,
                        sheet_headers,
                    )
                    logger.info(f"Extracted data from {file_name}")
                    # Add the file ID to the set of processed files
                    processed_file_ids.add(file_id)
                else:
                    logger.info(f"File {file_name} has already been processed.")

            # Save the processed file IDs to a file
            save_processed_file_ids("processed_files.txt", processed_file_ids)

    except Exception as e:
        logger.critical(f"An unexpected error occurred in the main function: {e}")


if __name__ == "__main__":
    main()
