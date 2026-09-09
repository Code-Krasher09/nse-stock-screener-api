"""
Pydantic schemas for API requests and responses.
"""
from datetime import date

from pydantic import BaseModel


class ScreenRequest(BaseModel):
    price_min: float | None = None
    price_max: float | None = None
    volume_min: float | None = None
    rsi_min: float | None = None
    rsi_max: float | None = None
    macd_min: float | None = None
    macd_max: float | None = None
    # Note for Phase 5+: Add complex boolean crossover logic here (e.g. macd_crossover_signal)


class IndicatorResponse(BaseModel):
    date: date
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    bb_upper: float | None = None
    bb_lower: float | None = None
    bb_mid: float | None = None


class PriceResponse(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


class StockBase(BaseModel):
    symbol: str
    company_name: str | None = None
    sector: str | None = None


class StockLatestResponse(StockBase):
    latest_price: float | None = None
    latest_volume: float | None = None
    indicators: IndicatorResponse | None = None


class StockHistoryResponse(StockBase):
    history: list[PriceResponse] = []
    indicators: list[IndicatorResponse] = []

