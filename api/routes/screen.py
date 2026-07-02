"""
API routes for stock screening based on technical indicators.
"""
import json
import hashlib
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from db.models import Stock, PriceHistory, Indicator
from api.deps import get_db
from api.schemas import ScreenRequest, StockLatestResponse
from db.cache import get_cache, set_cache

router = APIRouter()

@router.post("", response_model=list[StockLatestResponse])
async def run_screener(request: ScreenRequest, db: AsyncSession = Depends(get_db)):
    """
    Execute the screener against current stock data.
    Note for Phase 5+: Add complex boolean crossover logic here.
    """
    # Create SHA256 hash of the sorted request payload for cache key
    req_dict = request.model_dump(exclude_unset=True)
    sorted_req_str = json.dumps(req_dict, sort_keys=True)
    req_hash = hashlib.sha256(sorted_req_str.encode('utf-8')).hexdigest()
    cache_key = f"screen_{req_hash}"
    
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    # Use max_date subquery to filter only the latest data
    subq_date = select(PriceHistory.stock_id, func.max(PriceHistory.date).label('max_date')).group_by(PriceHistory.stock_id).subquery()
    
    stmt = (
        select(Stock, PriceHistory, Indicator)
        .join(PriceHistory, and_(Stock.id == PriceHistory.stock_id, PriceHistory.date == subq_date.c.max_date))
        .outerjoin(Indicator, and_(Stock.id == Indicator.stock_id, Indicator.date == subq_date.c.max_date))
        .where(Stock.is_active == True)
    )
    
    # Apply scalar filters
    if request.price_min is not None:
        stmt = stmt.where(PriceHistory.close >= request.price_min)
    if request.price_max is not None:
        stmt = stmt.where(PriceHistory.close <= request.price_max)
    if request.volume_min is not None:
        stmt = stmt.where(PriceHistory.volume >= request.volume_min)
        
    if request.rsi_min is not None:
        stmt = stmt.where(Indicator.rsi >= request.rsi_min)
    if request.rsi_max is not None:
        stmt = stmt.where(Indicator.rsi <= request.rsi_max)
        
    if request.macd_min is not None:
        stmt = stmt.where(Indicator.macd >= request.macd_min)
    if request.macd_max is not None:
        stmt = stmt.where(Indicator.macd <= request.macd_max)
        
    result = await db.execute(stmt)
    rows = result.all()
    
    response = []
    for stock, price, indicator in rows:
        response.append({
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "latest_price": price.close if price else None,
            "latest_volume": price.volume if price else None,
            "indicators": {
                "date": indicator.date.isoformat(),
                "rsi": indicator.rsi,
                "macd": indicator.macd,
                "macd_signal": indicator.macd_signal,
                "macd_hist": indicator.macd_hist,
                "bb_upper": indicator.bb_upper,
                "bb_lower": indicator.bb_lower,
                "bb_mid": indicator.bb_mid,
            } if indicator else None
        })
        
    await set_cache(cache_key, response, ttl=120) # 2-minute TTL
    return response
