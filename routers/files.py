from fastapi import APIRouter, Depends, HTTPException
from services.file_processor import process_new_files
from utils.common import load_processed_file_ids
from services.google_services import get_services
from models.schemas import ProcessResponse, FilesResponse
from utils.logger import logger

router = APIRouter(
    prefix="/files", tags=["Files"], responses={404: {"description": "Not found"}}
)


@router.get(
    "/",
    response_model=FilesResponse,
    summary="Get Processed Files",
    description="Retrieve a list of all processed file IDs.",
)
async def get_processed_files():
    """
    Retrieve a list of all processed file IDs.
    """
    try:
        processed_file_ids = load_processed_file_ids("processed_files.txt")
        return {"processed_file_ids": list(processed_file_ids)}
    except Exception as e:
        logger.error(f"Error getting Processed files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.post(
    "/process",
    response_model=ProcessResponse,
    summary="Trigger File Processing",
    description="Manually trigger the file processing job to check for new files and process them.",
)
async def trigger_processing(
    drive_service=Depends(get_services("drive")),
    sheets_service=Depends(get_services("sheets")),
):
    """
    Manually trigger the file processing job to check for new files and process them.
    """
    try:
        process_new_files(drive_service, sheets_service)
        return {"message": "File processing triggered."}
    except Exception as e:
        logger.error(f"Error Processing Files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
