# app/routers/file_processor.py
from fastapi import APIRouter, HTTPException, Query
from services.file_processor import process_file
from services.google_services import load_service_account_credentials
from googleapiclient.discovery import build
from utils.logger import logger
import os

router = APIRouter()

@router.post("/pdf", response_model=dict)
def process_pdf_file(
    file_path: str = Query(..., description="The path to the PDF file to process."),
    spreadsheet_id: str = Query(..., description="The ID of the Google Spreadsheet.")
):
    try:
        SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        SCOPES = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        credentials = load_service_account_credentials(SERVICE_ACCOUNT_FILE, SCOPES)
        drive_service = build("drive", "v3", credentials=credentials)
        sheets_service = build("sheets", "v4", credentials=credentials)
        
        # Assuming sheet_headers is defined somewhere or passed as a parameter
        from utils.common import sheet_headers
        
        # Process the file
        process_file(
            file_name=os.path.basename(file_path),
            file_path=file_path,
            sheets_service=sheets_service,
            SPREADSHEET_ID=spreadsheet_id,
            sheet_headers=sheet_headers,
        )
        
        logger.info(f"Processed file: {file_path}")
        return {"message": f"Successfully processed file: {file_path}"}
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
