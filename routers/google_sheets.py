# app/routers/google_sheets.py
from fastapi import APIRouter, HTTPException, Query
from typing import List
from services.google_services import append_to_google_sheets, list_files_in_drive, load_service_account_credentials
from googleapiclient.discovery import build
from utils.logger import logger
import os

router = APIRouter()

@router.get("/data", response_model=List[List[str]])
def fetch_google_sheet_data(
    spreadsheet_id: str = Query(..., description="The ID of the Google Spreadsheet."),
    range_name: str = Query(..., description="The range of cells to retrieve, e.g., 'Sheet1!A1:D10'.")
):
    try:
        SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        credentials = load_service_account_credentials(SERVICE_ACCOUNT_FILE, SCOPES)
        sheets_service = build('sheets', 'v4', credentials=credentials)
        data = append_to_google_sheets(sheets_service, spreadsheet_id, range_name, [])
        return data
    except Exception as e:
        logger.error(f"Error fetching Google Sheets data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
