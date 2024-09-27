import os
import time
import uuid
import threading
import json
from googleapiclient.discovery import build
from services.google_services import load_service_account_credentials
from utils.logger import logger
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
FOLDER_ID = os.getenv("FOLDER_ID")
SCOPES = ["https://www.googleapis.com/auth/drive"]
WATCH_EXPIRATION_BUFFER = 60000  # Renew 1 minute before expiration (in milliseconds)

WATCH_INFO_FILE = "watch_info.json"
START_PAGE_TOKEN_FILE = "start_page_token.txt"


def save_watch_info(watch_info):
    with open(WATCH_INFO_FILE, "w") as f:
        json.dump(watch_info, f)


def load_watch_info():
    if os.path.exists(WATCH_INFO_FILE):
        with open(WATCH_INFO_FILE, "r") as f:
            return json.load(f)
    return None


def save_start_page_token(token):
    with open(START_PAGE_TOKEN_FILE, "w") as f:
        f.write(token)


def load_start_page_token():
    if os.path.exists(START_PAGE_TOKEN_FILE):
        with open(START_PAGE_TOKEN_FILE, "r") as f:
            return f.read()
    return None


def setup_watch():
    credentials = load_service_account_credentials(SERVICE_ACCOUNT_FILE, SCOPES)
    drive_service = build("drive", "v3", credentials=credentials)

    # Generate a unique channel ID
    channel_id = str(uuid.uuid4())
    webhook_address = "https://webhook.site/419ea69a-8ce0-43ae-8faf-440e401c5281/webhook"  # Replace with your webhook URL

    # Get the start page token
    start_page_token_response = drive_service.changes().getStartPageToken().execute()
    start_page_token = start_page_token_response.get("startPageToken")
    save_start_page_token(start_page_token)

    channel = {
        "id": channel_id,
        "type": "web_hook",
        "address": webhook_address,
        # Optionally, set the expiration time (max 7 days in milliseconds)
        # 'expiration': str(int(time.time() * 1000) + 604800000),  # 7 days
    }

    try:
        # Set up the watch on the Drive changes feed using the start page token
        response = (
            drive_service.changes()
            .watch(
                body=channel,
                pageToken=start_page_token,
                fields="*",  # Optional: specify fields to include in the response
            )
            .execute()
        )
        logger.info(f"Watch setup response: {response}")

        # Save watch information
        watch_info = {
            "channel_id": response.get("id"),
            "resource_id": response.get("resourceId"),
            "expiration": response.get("expiration"),
        }
        save_watch_info(watch_info)
        logger.info(f"Watch will expire at {watch_info['expiration']}")

    except HttpError as error:
        logger.error(f"An error occurred while setting up the watch: {error}")


def renew_watch():
    credentials = load_service_account_credentials(SERVICE_ACCOUNT_FILE, SCOPES)
    drive_service = build("drive", "v3", credentials=credentials)

    watch_info = load_watch_info()
    if watch_info:
        channel_id = watch_info.get("channel_id")
        resource_id = watch_info.get("resource_id")

        # Stop the existing watch
        try:
            drive_service.channels().stop(
                body={
                    "id": channel_id,
                    "resourceId": resource_id,
                }
            ).execute()
            logger.info(f"Stopped existing watch with channel ID {channel_id}")
        except HttpError as error:
            logger.error(f"An error occurred while stopping the watch: {error}")

    # Set up a new watch
    setup_watch()


def watch_renewal_scheduler():
    while True:
        watch_info = load_watch_info()
        if watch_info and "expiration" in watch_info:
            expiration_time_ms = int(watch_info["expiration"])
            current_time_ms = int(time.time() * 1000)
            time_until_expiration = expiration_time_ms - current_time_ms
            if time_until_expiration <= WATCH_EXPIRATION_BUFFER:
                logger.info("Watch is about to expire, renewing watch...")
                renew_watch()
                # Wait a minute before the next check
                time.sleep(60)
            else:
                sleep_time = (time_until_expiration - WATCH_EXPIRATION_BUFFER) / 1000
                logger.info(f"Next watch renewal check in {sleep_time} seconds")
                time.sleep(sleep_time)
        else:
            # No watch info, set up a new watch
            logger.info("No existing watch found, setting up a new watch...")
            setup_watch()
            # Wait before the next check
            time.sleep(60)  # Check every minute if no expiration info is available


if __name__ == "__main__":
    # Start the watch renewal scheduler in a separate thread
    threading.Thread(target=watch_renewal_scheduler, daemon=True).start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Watch renewal scheduler stopped.")
