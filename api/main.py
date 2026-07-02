from contextlib import asynccontextmanager
from fastapi import FastAPI

import logging

from db.session import engine, async_session_maker
from db.models import Base
from api.routes import health, stocks, screen, ingest
from ingestion.scheduler import start_scheduler, scheduler

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database schema on startup (Phase 1 approach)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Start APScheduler
    start_scheduler(async_session_maker)
    
    yield
    
    # Cleanup on shutdown (if needed)
    scheduler.shutdown()
    await engine.dispose()

app = FastAPI(
    title="NSE Stock Screener API",
    description="A real-time REST API for screening NSE equities.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(health.router, tags=["Health"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
app.include_router(screen.router, prefix="/screen", tags=["Screening"])
