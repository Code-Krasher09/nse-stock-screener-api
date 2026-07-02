"""
API routes for triggering data ingestion.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from api.deps import get_db
from ingestion.fetcher import fetch_and_store_data

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingestion(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Manually trigger the data ingestion pipeline in the background.
    """
    logger.info("Manual ingestion trigger received.")
    background_tasks.add_task(fetch_and_store_data, db)
    return {"message": "Ingestion job started in the background."}
