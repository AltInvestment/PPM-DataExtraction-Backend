import os
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload
from utils.logger import logger

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
        # Extract text from the first few lines of the PDF
        text = extract_text(file_path)
        return text
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
