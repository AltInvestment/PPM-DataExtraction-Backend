import os
from fastapi import FastAPI
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from utils.logger import logger
from services.google_services import (
    load_service_account_credentials,
    initialize_google_services,
)
from services.background_tasks import start_background_tasks, shutdown_background_tasks
from routers import files_router, data_router
from fastapi.middleware.cors import CORSMiddleware


# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Global variables to store services
credentials = None
drive_service = None
sheets_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global credentials, drive_service, sheets_service

    try:
        # Get variables from .env file
        SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
        if not SERVICE_ACCOUNT_FILE:
            logger.error("SERVICE_ACCOUNT_FILE environment variable is missing.")
            raise Exception("Missing SERVICE_ACCOUNT_FILE")

        # Define the required scopes
        SCOPES = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ]

        # Load credentials and create service objects
        credentials = load_service_account_credentials(SERVICE_ACCOUNT_FILE, SCOPES)
        drive_service, sheets_service = initialize_google_services(credentials)

        # Start background tasks
        start_background_tasks(drive_service, sheets_service)

        yield

    finally:
        # Shutdown background tasks
        shutdown_background_tasks()
        logger.info("Application shutdown completed.")


# Re-initialize FastAPI app with lifespan
app = FastAPI(
    title="File Processing API",
    description="API to process PDF files from Google Drive and update Google Sheets.",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Files",
            "description": "Operations related to file processing.",
        },
        {
            "name": "Data",
            "description": "Operations for retrieving data and files.",
        },
    ],
    lifespan=lifespan,
)
# CORS Configuration
origins = [
    "http://localhost",  # React development server
    "http://localhost:3000",  # Default port for Create React App
    "https://your-production-domain.com",  # Replace with your production domain
    # Add other origins as needed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(files_router)
app.include_router(data_router)

# Exception handler
from fastapi import Request
from fastapi.responses import JSONResponse


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"An error occurred: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal error occurred."},
    )
