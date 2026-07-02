"""
Scheduler for periodic data ingestion tasks.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from ingestion.fetcher import fetch_and_store_data

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def start_scheduler(session_maker):
    """
    Initialize and start APScheduler.
    """
    async def job():
        logger.info("Running scheduled ingestion job...")
        async with session_maker() as session:
            await fetch_and_store_data(session)

    # Hourly cron during 09:15-15:30 IST
    # Runs at 09:15, 10:15, 11:15, 12:15, 13:15, 14:15, 15:15
    scheduler.add_job(
        job,
        CronTrigger(hour='9-15', minute='15', timezone='Asia/Kolkata'),
        id='market_hours_ingestion',
        name='Hourly Market Data Ingestion',
        replace_existing=True
    )
    
    # One EOD run at 16:00 IST
    scheduler.add_job(
        job,
        CronTrigger(hour='16', minute='0', timezone='Asia/Kolkata'),
        id='eod_ingestion',
        name='End of Day Data Ingestion',
        replace_existing=True
    )

    scheduler.start()
    logger.info("APScheduler started with market-hours and EOD jobs.")
