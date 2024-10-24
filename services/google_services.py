import os
from fastapi import HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload
from utils.logger import logger


_drive_service = None
_sheets_service = None


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


def initialize_google_services(credentials):
    global _drive_service, _sheets_service
    try:
        _drive_service = build("drive", "v3", credentials=credentials)
        _sheets_service = build("sheets", "v4", credentials=credentials)
        logger.info("Google Drive and Sheets services initialized.")
        return _drive_service, _sheets_service
    except Exception as e:
        logger.error(f"Failed to initialize Google services: {e}")
        raise


def get_services(service_name):
    def _get_service():
        if service_name == "drive":
            return _drive_service
        elif service_name == "sheets":
            return _sheets_service
        else:
            raise ValueError("Invalid service name")

    return _get_service


def list_files_in_drive(drive_service, folder_id):
    file_data = []
    try:
        results = (
            drive_service.files()
            .list(
                q=f"'{folder_id}' in parents and mimeType='application/pdf'",
                pageSize=1000,
                fields="files(id, name)",
            )
            .execute()
        )
        files = results.get("files", [])

        if not files:
            logger.info("No files found in the specified folder.")
        else:
            logger.info(f"Found {len(files)} files in the folder.")
            for file in files:
                logger.info(f'{file["name"]} ({file["id"]})')

                # Download PDF file
                logger.info(f"Downloading PDF file: {file['name']}")
                file_path = download_pdf_from_drive(
                    drive_service, file["id"], file["name"]
                )
                if file_path:
                    # Return file ID, name, and path
                    file_data.append((file["id"], file["name"], file_path))
    except HttpError as error:
        logger.error(f"An error occurred while listing files in Drive: {error}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

    return file_data


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


def delete_last_row(sheets_service, spreadsheet_id, sheet_name):
    try:
        # Get the properties of the sheet to find the sheet ID
        sheet_metadata = (
            sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        )
        sheets = sheet_metadata.get("sheets", "")
        sheet_id = None
        for sheet in sheets:
            if sheet.get("properties", {}).get("title", "") == sheet_name:
                sheet_id = sheet.get("properties", {}).get("sheetId", 0)
                break

        if sheet_id is None:
            logger.error("Sheet %s not found.", sheet_name)
            return

        # Get the number of rows in the sheet
        sheet_info = (
            sheets_service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=sheet_name)
            .execute()
        )
        num_rows = len(sheet_info.get("values", []))

        if num_rows < 1:
            logger.warning("Sheet %s is empty. No rows to delete.", sheet_name)
            return

        # Build the request to delete the last row
        request_body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": num_rows - 1,  # Zero-based index
                            "endIndex": num_rows,  # Exclude end index
                        }
                    }
                }
            ]
        }

        response = (
            sheets_service.spreadsheets()
            .batchUpdate(spreadsheetId=spreadsheet_id, body=request_body)
            .execute()
        )
        logger.info("Deleted the last row in sheet %s.", sheet_name)
    except Exception as e:
        logger.error("An error occurred while deleting the last row: %s", e)


def get_data_from_sheets(sheets_service, spreadsheet_id, deal_id):
    try:
        # Get the spreadsheet metadata to retrieve all sheet names
        sheet_metadata = (
            sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        )
        sheets = sheet_metadata.get("sheets", "")
        sheet_names = [sheet.get("properties", {}).get("title", "") for sheet in sheets]

        deal_data = {}

        for sheet_name in sheet_names:
            # Fetch data from the current sheet
            result = (
                sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=sheet_name)
                .execute()
            )
            values = result.get("values", [])
            if not values:
                continue  # Skip empty sheets

            headers = values[0]
            if "Deal_ID" not in headers:
                continue  # Skip sheets without Deal_ID column

            data_rows = values[1:]

            # Find rows where Deal_ID matches
            deal_id_index = headers.index("Deal_ID")
            matching_rows = [
                dict(zip(headers, row))
                for row in data_rows
                if len(row) > deal_id_index and row[deal_id_index] == deal_id
            ]

            if matching_rows:
                deal_data[sheet_name] = matching_rows

        return deal_data

    except Exception as e:
        logger.error(f"An error occurred while fetching data from Sheets: {e}")
        raise HTTPException(
            status_code=429, detail="API Limit Reached"
        )


def get_all_deal_ids(sheets_service, spreadsheet_id):
    """
    Fetch all unique Deal_IDs from the Google Sheet.

    Parameters:
    - sheets_service: The Google Sheets service instance.
    - spreadsheet_id: The ID of the Google Spreadsheet.

    Returns:
    - A list of unique Deal_IDs.
    """
    try:
        # Get the spreadsheet metadata to retrieve all sheet names
        sheet_metadata = (
            sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        )
        sheets = sheet_metadata.get("sheets", "")
        sheet_names = [sheet.get("properties", {}).get("title", "") for sheet in sheets]

        deal_ids = set()

        for sheet_name in sheet_names:
            # Fetch data from the current sheet
            result = (
                sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=sheet_name)
                .execute()
            )
            values = result.get("values", [])
            if not values:
                continue  # Skip empty sheets

            headers = values[0]
            if "Deal_ID" not in headers:
                continue  # Skip sheets without Deal_ID column

            data_rows = values[1:]
            deal_id_index = headers.index("Deal_ID")

            # Collect Deal_IDs from the current sheet
            for row in data_rows:
                if len(row) > deal_id_index:
                    deal_id = row[deal_id_index]
                    deal_ids.add(deal_id)

        return list(deal_ids)

    except Exception as e:
        logger.error(f"An error occurred while fetching Deal_IDs from Sheets: {e}")
        return []
