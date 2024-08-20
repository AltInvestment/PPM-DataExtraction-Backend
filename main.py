import os
import logging
from utils.logger import logger
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload
from pdfminer.high_level import extract_text

# Load environment variables from .env file
load_dotenv()

# Suppress pdfminer logging
logging.getLogger("pdfminer").setLevel(logging.WARNING)


def load_service_account_credentials(service_account_file, scopes):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        logger.info("Service account credentials loaded successfully.")
        return credentials
    except Exception as e:
        logger.error(f"Failed to load service account credentials: {e}")
        raise


def download_pdf_from_drive(drive_service, file_id, file_name):
    try:
        # Create the tmp directory if it doesn't exist
        if not os.path.exists("tmp"):
            os.makedirs("tmp")

        # File path where the PDF will be saved
        file_path = os.path.join("tmp", file_name)

        request = drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.info(f"Download {int(status.progress() * 100)}%.")

        logger.info(f"File {file_name} downloaded to {file_path}.")
        return file_path
    except HttpError as error:
        logger.error(f"An error occurred while downloading the file: {error}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def extract_text_from_pdf(file_path):
    try:
        logger.info(f"Extracting text from {file_path}...")
        # Extract text from the first few lines of the PDF
        text = extract_text(file_path)
        snippet = text[:500]  # Adjust the number of characters as needed
        return snippet
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        return ""


def list_files_in_drive(drive_service, folder_id):
    file_data = []
    try:
        results = (
            drive_service.files()
            .list(
                q=f"'{folder_id}' in parents",
                pageSize=10,
                fields="files(id, name, mimeType)",
            )
            .execute()
        )
        files = results.get("files", [])

        if not files:
            logger.info("No files found in the specified folder.")
        else:
            logger.info("Files found:")
            for file in files:
                logger.info(f'{file["name"]} ({file["id"]})')

                # Check if the file is a PDF
                if file["mimeType"] == "application/pdf":
                    logger.info(f"Downloading PDF file: {file['name']}")
                    file_path = download_pdf_from_drive(
                        drive_service, file["id"], file["name"]
                    )
                    if file_path:
                        extracted_text = extract_text_from_pdf(file_path)
                        file_data.append([file["name"], extracted_text])
    except HttpError as error:
        logger.error(f"An error occurred while listing files in Drive: {error}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

    return file_data


def append_to_google_sheets(sheets_service, spreadsheet_id, range_name, values):
    try:
        body = {"values": values}
        result = (
            sheets_service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )
        logger.info(
            f'{result.get("updates").get("updatedCells")} cells appended to Google Sheets.'
        )
    except HttpError as error:
        logger.error(
            f"An error occurred while appending data to Google Sheets: {error}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


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

        # Append the file name and extracted text to Google Sheets
        if file_data:
            RANGE_NAME = "Sheet1!A1:B1"  # Adjust the range as necessary
            append_to_google_sheets(
                sheets_service, SPREADSHEET_ID, RANGE_NAME, file_data
            )

    except Exception as e:
        logger.critical(f"An unexpected error occurred in the main function: {e}")


if __name__ == "__main__":
    main()
