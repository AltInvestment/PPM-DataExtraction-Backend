from fastapi import APIRouter, Depends
from services.file_processor import process_new_files
from utils.common import load_processed_file_ids
from services.google_services import get_services
from models.schemas import ProcessResponse, FilesResponse

router = APIRouter()


@router.get("/files", response_model=FilesResponse)
async def get_processed_files():
    processed_file_ids = load_processed_file_ids("processed_files.txt")
    return {"processed_file_ids": list(processed_file_ids)}


@router.post("/process", response_model=ProcessResponse)
async def trigger_processing(
    drive_service=Depends(get_services("drive")),
    sheets_service=Depends(get_services("sheets")),
):
    process_new_files(drive_service, sheets_service)
    return {"message": "File processing triggered."}
