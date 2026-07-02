"""
API routes for system health checks.
"""
import asyncio
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from api.deps import get_db
from ingestion.scheduler import scheduler
from db.cache import redis_client

router = APIRouter()

@router.get("", status_code=status.HTTP_200_OK)
async def check_health(response: Response, db: AsyncSession = Depends(get_db)):
    """
    Check the health of the API, Database, Redis, and Scheduler.
    Returns 200 OK if all healthy, 207 Multi-Status if some degraded/down.
    """
    health_status = {
        "status": "ok",
        "services": {}
    }
    
    # 1. Check Database
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=2.0)
        health_status["services"]["database"] = "up"
    except asyncio.TimeoutError:
        health_status["services"]["database"] = "degraded"
        health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["database"] = "down"
        health_status["status"] = "degraded"
        
    # 2. Check Redis
    try:
        await asyncio.wait_for(redis_client.ping(), timeout=2.0)
        health_status["services"]["redis"] = "up"
    except asyncio.TimeoutError:
        health_status["services"]["redis"] = "degraded"
        health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["redis"] = "down"
        health_status["status"] = "degraded"
        
    # 3. Check Scheduler
    try:
        jobs = scheduler.get_jobs()
        next_run = jobs[0].next_run_time.isoformat() if jobs and hasattr(jobs[0], 'next_run_time') else None
        health_status["services"]["scheduler"] = {
            "state": "running" if scheduler.running else "stopped",
            "next_run_time": next_run
        }
    except Exception:
        health_status["services"]["scheduler"] = {
            "state": "unknown",
            "next_run_time": None
        }
        
    if health_status["status"] == "degraded":
        response.status_code = status.HTTP_207_MULTI_STATUS
        
    return health_status
