"""
Technical indicator computation engine.
"""
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from db.models import PriceHistory, Indicator
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.bollinger import calculate_bollinger_bands

logger = logging.getLogger(__name__)

async def compute_and_store_indicators(session: AsyncSession, stock_ids: list[int]):
    """
    Compute technical indicators for given stocks and store in DB.
    Uses 60 calendar days lookback to guarantee 35+ trading days.
    """
    if not stock_ids:
        return
        
    start_time = time.time()
    
    # Calculate 60 days ago
    cutoff_date = (datetime.utcnow() - timedelta(days=60)).date()
    
    # Fetch historical prices for these stocks
    stmt = select(PriceHistory).where(
        PriceHistory.stock_id.in_(stock_ids),
        PriceHistory.date >= cutoff_date
    ).order_by(PriceHistory.stock_id, PriceHistory.date)
    
    result = await session.execute(stmt)
    prices = result.scalars().all()
    
    if not prices:
        logger.warning(f"No price history found for {len(stock_ids)} stocks.")
        return
        
    # Convert to DataFrame
    df = pd.DataFrame([{
        'stock_id': p.stock_id,
        'date': p.date,
        'close': p.close
    } for p in prices])
    
    indicator_records = []
    nan_count = 0
    
    for stock_id, group in df.groupby('stock_id'):
        group = group.sort_values('date').set_index('date')
        close_series = group['close']
        
        if len(close_series) < 35:
            # Insufficient data for MACD (requires 26+9=35)
            nan_count += 1
            
        rsi_series = calculate_rsi(close_series)
        macd_line, macd_signal, macd_hist = calculate_macd(close_series)
        bb_upper, bb_lower, bb_mid = calculate_bollinger_bands(close_series)
        
        res_df = pd.DataFrame({
            'rsi': rsi_series,
            'macd': macd_line,
            'macd_signal': macd_signal,
            'macd_hist': macd_hist,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'bb_mid': bb_mid
        })
        
        # Drop rows where all indicators are NaN
        res_df = res_df.dropna(how='all')
        
        for date, row in res_df.iterrows():
            indicator_records.append({
                "stock_id": stock_id,
                "date": date,
                "rsi": None if pd.isna(row['rsi']) else float(row['rsi']),
                "macd": None if pd.isna(row['macd']) else float(row['macd']),
                "macd_signal": None if pd.isna(row['macd_signal']) else float(row['macd_signal']),
                "macd_hist": None if pd.isna(row['macd_hist']) else float(row['macd_hist']),
                "bb_upper": None if pd.isna(row['bb_upper']) else float(row['bb_upper']),
                "bb_lower": None if pd.isna(row['bb_lower']) else float(row['bb_lower']),
                "bb_mid": None if pd.isna(row['bb_mid']) else float(row['bb_mid']),
            })
            
    if indicator_records:
        stmt = insert(Indicator).values(indicator_records)
        stmt = stmt.on_conflict_do_update(
            constraint='uq_indicator_stock_date',
            set_={
                "rsi": stmt.excluded.rsi,
                "macd": stmt.excluded.macd,
                "macd_signal": stmt.excluded.macd_signal,
                "macd_hist": stmt.excluded.macd_hist,
                "bb_upper": stmt.excluded.bb_upper,
                "bb_lower": stmt.excluded.bb_lower,
                "bb_mid": stmt.excluded.bb_mid,
            }
        )
        await session.execute(stmt)
        await session.commit()
        
    duration = time.time() - start_time
    logger.info(f"Computed indicators for {len(stock_ids)} stocks in {duration:.2f}s. {nan_count} stocks had insufficient history.")
