from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from services.google_services import (
    get_data_from_sheets,
    get_services,
    get_all_deal_ids,
)
from models.schemas import DataResponse, DealIDsResponse
import os
from utils.logger import logger

router = APIRouter(
    prefix="/data", tags=["Data"], responses={404: {"description": "Not found"}}
)


@router.get(
    "/deal_ids",
    response_model=DealIDsResponse,
    summary="Get All Deal_IDs",
    description="Retrieve all unique Deal_IDs from the Google Sheet.",
)
async def get_all_deal_ids_endpoint(sheets_service=Depends(get_services("sheets"))):
    """
    Retrieve all unique Deal_IDs from the Google Sheet.

    - **Returns**: A JSON object containing a list of all Deal_IDs.
    """
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    deal_ids = get_all_deal_ids(sheets_service, SPREADSHEET_ID)
    if not deal_ids:
        raise HTTPException(status_code=404, detail="No Deal_IDs found.")
    return {"deal_ids": deal_ids}


@router.get(
    "/{deal_id}",
    response_model=DataResponse,
    summary="Get Deal Data",
    description="Retrieve data for a specific Deal_ID from all relevant sheets.",
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "deal_id": "SampleDealID",
                        "data": {
                            "Final Data Table": [
                                {
                                    "Deal_ID": "SampleDealID",
                                    "Sponsor": "Sponsor Name",
                                    "Deal_Title": "Deal Title",
                                    # ... other fields ...
                                }
                            ],
                            # ... other sheets ...
                        },
                    }
                }
            },
        },
        404: {"description": "Data not found for the given Deal_ID."},
    },
)
async def get_file_data(deal_id: str, sheets_service=Depends(get_services("sheets"))):
    """
    Retrieve data for a specific Deal_ID from all relevant sheets.

    - **Parameters**:
        - `deal_id`: The unique identifier for the deal.

    - **Returns**: A JSON object containing the deal data.
    """
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    data = get_data_from_sheets(sheets_service, SPREADSHEET_ID, deal_id)
    if not data:
        raise HTTPException(
            status_code=404, detail="Data not found for the given Deal_ID."
        )
    return {"deal_id": deal_id, "data": data}


@router.get(
    "/pdf/{deal_id}",
    summary="Get Original PDF",
    description="Retrieve the original PDF file associated with the given Deal_ID.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the original PDF file.",
        },
        400: {"description": "Invalid file path."},
        404: {"description": "File not found."},
        500: {"description": "Internal server error."},
    },
)
async def get_pdf_file(deal_id: str):
    """
    Retrieve the original PDF file associated with the given Deal_ID.

    - **Parameters**:
        - `deal_id`: The unique identifier for the deal.

    - **Returns**: The original PDF file.
    """
    try:
        filename = f"{deal_id}.pdf"
        tmp_dir = os.path.abspath("tmp")
        file_path = os.path.join(tmp_dir, filename)

        if not file_path.startswith(tmp_dir):
            raise HTTPException(status_code=400, detail="Invalid file path.")
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="File not found.")

        return FileResponse(
            path=file_path, filename=filename, media_type="application/pdf"
        )
    except Exception as e:
        logger.error(f"Error serving PDF file for Deal_ID {deal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.get(
    "/pdf/{deal_id}/highlighted",
    summary="Get Highlighted PDF",
    description="Retrieve the highlighted PDF file associated with the given Deal_ID.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the highlighted PDF file.",
        },
        400: {"description": "Invalid file path."},
        404: {"description": "Highlighted file not found."},
        500: {"description": "Internal server error."},
    },
)
async def get_highlighted_pdf_file(deal_id: str):
    """
    Retrieve the highlighted PDF file associated with the given Deal_ID.

    - **Parameters**:
        - `deal_id`: The unique identifier for the deal.

    - **Returns**: The highlighted PDF file.
    """
    try:
        filename = f"{deal_id}.pdf_highlighted.pdf"
        tmp_dir = os.path.abspath("tmp")
        file_path = os.path.join(tmp_dir, filename)

        if not file_path.startswith(tmp_dir):
            raise HTTPException(status_code=400, detail="Invalid file path.")
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="Highlighted file not found.")

        return FileResponse(
            path=file_path, filename=filename, media_type="application/pdf"
        )
    except Exception as e:
        logger.error(f"Error serving highlighted PDF file for Deal_ID {deal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
