# app/routers/pdf_handler.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from utils.logger import logger

router = APIRouter()

# Directory to store uploaded PDFs
UPLOAD_DIRECTORY = os.getenv("PDF_UPLOAD_DIRECTORY", "uploads/")

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@router.post("/upload", response_model=dict)
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        logger.warning(f"Attempted to upload a non-PDF file: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    try:
        # Generate a unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        logger.info(f"Uploaded file {filename} with ID {file_id}")
        return {"file_id": file_id, "file_path": file_path}
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/path/{file_id}", response_model=dict)
def get_pdf_path(file_id: str):
    try:
        # Search for the file with the given file_id
        for filename in os.listdir(UPLOAD_DIRECTORY):
            if filename.startswith(file_id):
                file_path = os.path.join(UPLOAD_DIRECTORY, filename)
                logger.info(f"Retrieved path for file ID {file_id}: {file_path}")
                return {"file_id": file_id, "file_path": file_path}
        logger.warning(f"File ID {file_id} not found.")
        raise HTTPException(status_code=404, detail="File not found.")
    except Exception as e:
        logger.error(f"Error retrieving file path: {e}")
        raise HTTPException(status_code=500, detail=str(e))
