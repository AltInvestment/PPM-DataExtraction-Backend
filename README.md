# FastAPI PDF Processor

A FastAPI application that integrates with Google Sheets and Google Drive to upload, manage, and process PDF files. The application extracts data from PDFs using LangChain and OpenAI's GPT models, then appends the extracted data to Google Sheets.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
  - [1. Get Data from Google Sheets](#1-get-data-from-google-sheets)
  - [2. Upload/Get PDF File Path](#2-uploadget-pdf-file-path)
  - [3. File Processing](#3-file-processing)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Additional Considerations](#additional-considerations)
- [License](#license)

## Features

- **Google Sheets Integration**: Fetch and append data to Google Sheets.
- **Google Drive Integration**: List and download PDF files from a specific Google Drive folder.
- **PDF Uploading**: Upload PDF files via API.
- **File Processing**: Extract data from PDFs using LangChain and OpenAI's GPT models.
- **Logging**: Comprehensive logging for monitoring and debugging.
- **Environment Configuration**: Manage sensitive information using environment variables.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3.7+** installed on your machine.
- **Google Cloud Project** with Google Drive and Google Sheets APIs enabled.
- **Service Account** with the necessary credentials (`service-account.json`).
- **OpenAI API Key** for accessing GPT models.
- **Git** installed for version control (optional).

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/fastapi-pdf-processor.git
   cd fastapi-pdf-processor
   ```

2. **Create a Virtual Environment**

   It's recommended to use a virtual environment to manage dependencies.

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   Install the required Python packages using `pip`:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Environment Variables**

   Create a `.env` file in the root directory of the project and add the following variables:

   ```env
   DEAL_ID=your_deal_id
   SERVICE_ACCOUNT_FILE=path/to/your/service-account.json
   SPREADSHEET_ID=your_google_spreadsheet_id
   FOLDER_ID=your_google_drive_folder_id
   PDF_UPLOAD_DIRECTORY=uploads/
   GOOGLE_SERVICE_ACCOUNT_FILE=path/to/your/service-account.json
   OPENAI_API_KEY=your_openai_api_key
   ```

   - **DEAL_ID**: A unique identifier used during processing.
   - **SERVICE_ACCOUNT_FILE**: Path to your Google service account JSON file.
   - **SPREADSHEET_ID**: ID of the Google Spreadsheet to interact with.
   - **FOLDER_ID**: ID of the Google Drive folder to monitor for PDF files.
   - **PDF_UPLOAD_DIRECTORY**: Directory where uploaded PDFs will be stored.
   - **GOOGLE_SERVICE_ACCOUNT_FILE**: Path to your Google service account JSON file (same as `SERVICE_ACCOUNT_FILE`).
   - **OPENAI_API_KEY**: Your OpenAI API key for accessing GPT models.

2. **Directory Setup**

   Ensure the following directories exist:

   - **Uploads Directory**: For storing uploaded PDFs.

     ```bash
     mkdir uploads
     ```

   - **Logs Directory**: For storing application logs.

     ```bash
     mkdir logs
     ```

## Project Structure

```sh
fastapi-pdf-processor/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── google_sheets.py
│   │   ├── pdf_handler.py
│   │   └── file_processor.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_processor.py
│   │   ├── google_services.py
│   │   └── llm_processor.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── common.py
├── uploads/              # Directory to store uploaded PDFs
├── logs/                 # Directory to store log files
├── processed_files.txt   # File to keep track of processed files
├── .env                  # Environment variables
├── requirements.txt
└── README.md
```

- **`app/main.py`**: Entry point for the FastAPI application.
- **`app/routers/`**: Contains FastAPI route modules.
- **`app/services/`**: Existing service modules for processing files and interacting with Google APIs.
- **`app/utils/`**: Utility modules like logging and common functions.
- **`uploads/`**: Directory to store uploaded PDF files.
- **`logs/`**: Directory to store application logs.
- **`processed_files.txt`**: Keeps track of processed file IDs to prevent reprocessing.
- **`.env`**: Environment variables (ensure this file is **not** committed to version control).

## Running the Application

1. **Activate the Virtual Environment**

   If not already activated:

   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the FastAPI Application**

   Use Uvicorn to run the FastAPI server:

   ```bash
   uvicorn app.main:app --reload
   ```

   - **`--reload`**: Enables auto-reloading on code changes. Use only in development.

3. **Access the API**

   The API will be accessible at `http://127.0.0.1:8000`.

   - **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## API Endpoints

### 1. Get Data from Google Sheets

Fetch data from a specified range in a Google Spreadsheet.

- **Endpoint**: `GET /google-sheets/data`
- **Parameters**:
  - `spreadsheet_id` (query, required): The ID of the Google Spreadsheet.
  - `range_name` (query, required): The range of cells to retrieve (e.g., `Sheet1!A1:D10`).
- **Response**:
  - **200 OK**: Returns the requested data as a list of lists.
  - **500 Internal Server Error**: If an error occurs while fetching data.

#### Example Request

```http
GET /google-sheets/data?spreadsheet_id=your_spreadsheet_id&range_name=Sheet1!A1:D10
```

#### Example Response

```json
[
    ["Header1", "Header2", "Header3", "Header4"],
    ["Row1Col1", "Row1Col2", "Row1Col3", "Row1Col4"],
    ...
]
```

### 2. Upload/Get PDF File Path

#### a. Upload PDF

Upload a PDF file to the server.

- **Endpoint**: `POST /pdf/upload`
- **Body**:
  - `file` (form-data, required): The PDF file to upload.
- **Response**:
  - **200 OK**: Returns the `file_id` and `file_path` of the uploaded PDF.
  - **400 Bad Request**: If the uploaded file is not a PDF.
  - **500 Internal Server Error**: If an error occurs during upload.

##### Example Request

```http
POST /pdf/upload
Content-Type: multipart/form-data
Body: file=<your_pdf_file>
```

##### Example Response

```json
{
  "file_id": "unique-file-id",
  "file_path": "uploads/unique-file-id_filename.pdf"
}
```

#### b. Get PDF Path

Retrieve the file path of an uploaded PDF using its `file_id`.

- **Endpoint**: `GET /pdf/path/{file_id}`
- **Parameters**:
  - `file_id` (path, required): The unique ID of the uploaded PDF.
- **Response**:
  - **200 OK**: Returns the `file_id` and `file_path`.
  - **404 Not Found**: If the `file_id` does not exist.
  - **500 Internal Server Error**: If an error occurs during retrieval.

##### Example Request

```http
GET /pdf/path/unique-file-id
```

##### Example Response

```json
{
  "file_id": "unique-file-id",
  "file_path": "uploads/unique-file-id_filename.pdf"
}
```

### 3. File Processing

Process an uploaded PDF file by extracting data and appending it to Google Sheets.

- **Endpoint**: `POST /process/pdf`
- **Parameters**:
  - `file_path` (query, required): The path to the PDF file to process.
  - `spreadsheet_id` (query, required): The ID of the Google Spreadsheet to append data to.
- **Response**:
  - **200 OK**: Confirmation message indicating successful processing.
  - **500 Internal Server Error**: If an error occurs during processing.

#### Example Request

```http
POST /process/pdf?file_path=uploads/unique-file-id_filename.pdf&spreadsheet_id=your_spreadsheet_id
```

#### Example Response

```json
{
  "message": "Successfully processed file: uploads/unique-file-id_filename.pdf"
}
```

## Logging

Logs are stored in the `logs/` directory as `app.log`. The logger captures various levels of logs:

- **INFO**: General operational messages.
- **WARNING**: Indications of potential issues.
- **ERROR**: Errors that occur during execution.
- **CRITICAL**: Severe errors causing the application to terminate.

## Error Handling

The application uses FastAPI's exception handling to return meaningful HTTP responses:

- **400 Bad Request**: Invalid input or request parameters.
- **404 Not Found**: Requested resource does not exist.
- **500 Internal Server Error**: Unexpected server errors.

Ensure that proper error handling is implemented in all service modules to provide clear feedback to API consumers.

## Additional Considerations

### 1. **Background Tasks**

The original `main.py` script contains an infinite loop for continuously checking new files. In a FastAPI context, it's better to handle such tasks using background workers or scheduled jobs. Consider integrating tools like `Celery` or `APScheduler` for scheduled processing.

### 2. **Authentication & Security**

- **Authentication**: Protect your endpoints using OAuth2, JWT, or API keys to ensure only authorized users can access them.
- **Input Validation**: Validate and sanitize all inputs to prevent security vulnerabilities like injection attacks.
- **Secure File Uploads**: Limit the size of uploaded files and validate file types to prevent malicious uploads.

### 3. **Asynchronous Operations**

Leverage FastAPI's asynchronous capabilities to handle I/O-bound operations efficiently. Modify your service functions to be asynchronous (`async def`) if possible to improve performance.

### 4. **Testing**

Implement unit and integration tests using frameworks like `pytest` to ensure your endpoints and services work as expected. FastAPI provides excellent support for testing.

### 5. **Deployment**

While this README focuses on running the application locally, consider deploying your FastAPI application using platforms like AWS, Heroku, or DigitalOcean for production environments. Use production-ready ASGI servers like `Gunicorn` with `Uvicorn` workers for better performance.

## License

This project is licensed under the [MIT License](LICENSE).
