"""
SQLAlchemy database models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Stock(Base):
    """
    Model representing a stock equity.
    """
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prices = relationship("PriceHistory", back_populates="stock")


class PriceHistory(Base):
    """
    Model representing historical OHLCV data.
    """
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uq_stock_date'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock", back_populates="prices")


class Indicator(Base):
    """
    Model representing technical indicators for a stock on a specific date.
    """
    __tablename__ = "indicators"
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uq_indicator_stock_date'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    bb_mid = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stock = relationship("Stock")
