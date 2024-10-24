from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.file_processor import process_new_files
from utils.logger import logger

scheduler = AsyncIOScheduler()


def start_background_tasks(drive_service, sheets_service):
    # Add the periodic job to the scheduler
    scheduler.add_job(
        process_new_files,
        "interval",
        minutes=2,  # Adjust the interval as needed
        args=[drive_service, sheets_service],
        id="process_new_files_job",
    )
    scheduler.start()
    logger.info("Background tasks started.")


def shutdown_background_tasks():
    scheduler.shutdown()
    logger.info("Background tasks stopped.")
