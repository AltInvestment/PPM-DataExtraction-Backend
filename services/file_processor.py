import os
from services.google_services import list_files_in_drive
from utils.common import (
    load_processed_file_ids,
    save_processed_file_ids,
    sheet_headers,
)
from utils.logger import logger
from services.file_processor_helpers import process_file


def process_new_files(drive_service, sheets_service):
    try:
        SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
        FOLDER_ID = os.getenv("FOLDER_ID")

        if not SPREADSHEET_ID or not FOLDER_ID:
            logger.error(
                "One or more environment variables are missing. Please check the .env file."
            )
            return

        # Load processed file IDs
        processed_file_ids = load_processed_file_ids("processed_files.txt")

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
        logger.critical(f"An unexpected error occurred in process_new_files: {e}")
