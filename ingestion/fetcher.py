"""
Data fetcher for NSE stocks using yfinance.
"""
import asyncio
import logging
import pandas as pd
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
import urllib.request
import io

from db.models import Stock, PriceHistory
from indicators.engine import compute_and_store_indicators

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NIFTY_500_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

def get_nifty500_symbols() -> list[str]:
    """
    Fetch the NIFTY 500 symbols from NSE website.
    """
    try:
        req = urllib.request.Request(NIFTY_500_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            csv_data = response.read()
            
        df = pd.read_csv(io.BytesIO(csv_data))
        if 'Symbol' in df.columns:
            return df['Symbol'].tolist()
        else:
            logger.error(f"Expected 'Symbol' column not found in NSE CSV. Columns: {df.columns}")
            return []
    except Exception as e:
        logger.error(f"Failed to fetch NIFTY 500 list: {e}")
        return []

async def fetch_and_store_data(session: AsyncSession, symbols: list[str] = None):
    """
    Fetch OHLCV data for given symbols and store in database.
    If no symbols provided, fetches for NIFTY 500.
    """
    import time
    
    if not symbols:
        symbols = await asyncio.to_thread(get_nifty500_symbols)
        
    if not symbols:
        logger.error("No symbols to fetch.")
        return

    total_start_time = time.time()
    batch_size = 100
    
    # yfinance requires .NS suffix for NSE stocks
    yf_symbols = [f"{sym}.NS" for sym in symbols]
    
    batches = [yf_symbols[i:i + batch_size] for i in range(0, len(yf_symbols), batch_size)]
    symbol_batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
    
    logger.info(f"Fetching data for {len(yf_symbols)} symbols in {len(batches)} batches of {batch_size}...")
    
    batch_times = []
    
    for i, (batch_yf, batch_sym) in enumerate(zip(batches, symbol_batches)):
        batch_start_time = time.time()
        
        # Exponential backoff retry loop
        max_retries = 3
        retry_delay = 2
        success = False
        data = None
        
        for attempt in range(max_retries):
            try:
                data = await asyncio.to_thread(
                    yf.download, 
                    tickers=batch_yf, 
                    period="1mo",
                    interval="1d",
                    group_by="ticker",
                    auto_adjust=True,
                    threads=True
                )
                success = True
                break
            except Exception as e:
                logger.error(f"Batch {i+1} failed attempt {attempt+1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
        
        if not success or data is None or data.empty:
            logger.error(f"Batch {i+1} completely failed after {max_retries} retries.")
            continue

        # Process and store data for this batch
        stock_records = [{"symbol": sym, "is_active": True} for sym in batch_sym]
        
        stmt = insert(Stock).values(stock_records)
        stmt = stmt.on_conflict_do_update(
            index_elements=['symbol'],
            set_={"is_active": stmt.excluded.is_active}
        )
        await session.execute(stmt)
        await session.commit()
        
        result = await session.execute(select(Stock.id, Stock.symbol).where(Stock.symbol.in_(batch_sym)))
        stock_map = {row.symbol: row.id for row in result.all()}
        
        price_records = []
        
        if len(batch_yf) == 1:
            df = data.dropna()
            sym = batch_sym[0]
            stock_id = stock_map.get(sym)
            if stock_id:
                for date, row in df.iterrows():
                    price_records.append({
                        "stock_id": stock_id,
                        "date": date.date(),
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": float(row['Volume'])
                    })
        else:
            for sym, yf_sym in zip(batch_sym, batch_yf):
                stock_id = stock_map.get(sym)
                if not stock_id:
                    continue
                    
                if yf_sym not in data:
                    continue
                    
                df = data[yf_sym].dropna()
                for date, row in df.iterrows():
                    if pd.isna(row.get('Open')):
                        continue
                    price_records.append({
                        "stock_id": stock_id,
                        "date": date.date(),
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": float(row['Volume'])
                    })

        if price_records:
            stmt = insert(PriceHistory).values(price_records)
            stmt = stmt.on_conflict_do_update(
                constraint='uq_stock_date',
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume
                }
            )
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Stored {len(price_records)} price records for batch {i+1}.")
            
            # Compute and store indicators for this batch
            if stock_map:
                await compute_and_store_indicators(session, list(stock_map.values()))
        else:
            logger.warning(f"No valid price data found to store for batch {i+1}.")
            
        batch_end_time = time.time()
        batch_duration = batch_end_time - batch_start_time
        batch_times.append(batch_duration)
        logger.info(f"Processed batch {i+1}/{len(batches)} in {batch_duration:.2f}s")
        
        # 2-second pause between batches
        if i < len(batches) - 1:
            await asyncio.sleep(2)
            
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    avg_batch_time = sum(batch_times) / len(batch_times) if batch_times else 0
    
    logger.info(f"Ingestion completed in {total_duration:.2f}s. Avg batch time: {avg_batch_time:.2f}s")
