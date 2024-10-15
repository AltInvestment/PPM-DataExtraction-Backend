# app/main.py
from fastapi import FastAPI
from routers import google_sheets, pdf_handler, file_processor

app = FastAPI(
    title="My Python Project API",
    description="API for accessing Google Sheets data, handling PDF files, and processing files.",
    version="1.0.0"
)

# Include routers
app.include_router(google_sheets.router, prefix="/google-sheets", tags=["Google Sheets"])
app.include_router(pdf_handler.router, prefix="/pdf", tags=["PDF Handling"])
app.include_router(file_processor.router, prefix="/process", tags=["File Processing"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}
