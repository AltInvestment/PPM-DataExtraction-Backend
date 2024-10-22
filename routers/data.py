from fastapi import APIRouter, Depends
from services.google_services import get_data_from_sheets, get_services
from models.schemas import DataResponse
import os

router = APIRouter()


@router.get("/data/{deal_id}", response_model=DataResponse)
async def get_file_data(deal_id: str, sheets_service=Depends(get_services("sheets"))):
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    data = get_data_from_sheets(sheets_service, SPREADSHEET_ID, deal_id)
    return {"deal_id": deal_id, "data": data}
