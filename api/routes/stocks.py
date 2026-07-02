"""
API routes for stock data retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from db.models import Stock, PriceHistory, Indicator
from api.deps import get_db
from api.schemas import StockLatestResponse, StockHistoryResponse
from db.cache import get_cache, set_cache

router = APIRouter()

@router.get("", response_model=list[StockLatestResponse])
async def get_all_stocks(db: AsyncSession = Depends(get_db)):
    """
    Retrieve all active stocks with their latest price and indicators.
    Uses an optimized JOIN with a subquery to fetch the latest date per stock, avoiding N+1 queries.
    """
    cache_key = "stocks_all_latest"
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    # Subquery to find the latest date per stock
    subq_price = select(PriceHistory.stock_id, func.max(PriceHistory.date).label('max_date')).group_by(PriceHistory.stock_id).subquery()
    
    stmt = (
        select(Stock, PriceHistory, Indicator)
        .outerjoin(PriceHistory, and_(Stock.id == PriceHistory.stock_id, PriceHistory.date == subq_price.c.max_date))
        .outerjoin(Indicator, and_(Stock.id == Indicator.stock_id, Indicator.date == subq_price.c.max_date))
        .where(Stock.is_active == True)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    response = []
    for stock, price, indicator in rows:
        stock_data = {
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
        }
        response.append(stock_data)
        
    await set_cache(cache_key, response, ttl=300) # 5-minute TTL
    return response

@router.get("/{symbol}", response_model=StockHistoryResponse)
async def get_stock_data(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve full historical data for a specific stock.
    """
    result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    stock = result.scalars().first()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
        
    prices_res = await db.execute(select(PriceHistory).where(PriceHistory.stock_id == stock.id).order_by(PriceHistory.date.desc()))
    indicators_res = await db.execute(select(Indicator).where(Indicator.stock_id == stock.id).order_by(Indicator.date.desc()))
    
    return {
        "symbol": stock.symbol,
        "company_name": stock.company_name,
        "sector": stock.sector,
        "history": prices_res.scalars().all(),
        "indicators": indicators_res.scalars().all()
    }
