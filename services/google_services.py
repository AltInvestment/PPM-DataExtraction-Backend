import os
import logging
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload
from pdfminer.high_level import extract_text
from utils.logger import logger

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
        while not done:
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


def watch_drive_folder(drive_service, folder_id):
    """Set up a watch on the specified Google Drive folder."""
    try:
        request_body = {
            "id": "unique-channel-id",  # Replace with your unique channel ID
            "type": "web_hook",
            "address": "https://your-webhook-url/webhook",  # Replace with your webhook URL
        }
        response = (
            drive_service.files().watch(fileId=folder_id, body=request_body).execute()
        )
        logger.info(f"Watch set up for folder {folder_id}: {response}")
    except HttpError as error:
        logger.error(f"An error occurred while setting up the watch: {error}")


def handle_file_upload(drive_service, sheets_service, file_id):
    """Handle the processing of a newly uploaded file."""
    try:
        file = (
            drive_service.files().get(fileId=file_id, fields="name, mimeType").execute()
        )
        file_name = file.get("name")
        mime_type = file.get("mimeType")

        if mime_type == "application/pdf":
            logger.info(f"Processing new PDF file: {file_name}")
            file_path = download_pdf_from_drive(drive_service, file_id, file_name)
            if file_path:
                extracted_text = extract_text_from_pdf(file_path)
                if extracted_text:
                    append_to_google_sheets(
                        sheets_service,
                        os.getenv("SPREADSHEET_ID"),
                        "Sheet1!A1:B1",  # Adjust the range as necessary
                        [[file_name, extracted_text]],
                    )
    except HttpError as error:
        logger.error(f"An error occurred while processing the file upload: {error}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
