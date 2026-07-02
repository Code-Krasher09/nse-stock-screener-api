"""
Pydantic schemas for API requests and responses.
"""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

class ScreenRequest(BaseModel):
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    volume_min: Optional[float] = None
    rsi_min: Optional[float] = None
    rsi_max: Optional[float] = None
    macd_min: Optional[float] = None
    macd_max: Optional[float] = None
    # Note for Phase 5+: Add complex boolean crossover logic here (e.g. macd_crossover_signal)

class IndicatorResponse(BaseModel):
    date: date
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_mid: Optional[float] = None

class PriceResponse(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float

class StockBase(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None

class StockLatestResponse(StockBase):
    latest_price: Optional[float] = None
    latest_volume: Optional[float] = None
    indicators: Optional[IndicatorResponse] = None

class StockHistoryResponse(StockBase):
    history: List[PriceResponse] = []
    indicators: List[IndicatorResponse] = []
