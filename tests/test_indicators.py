"""
Unit tests for technical indicators.
"""
import pytest
import pandas as pd
import numpy as np
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.bollinger import calculate_bollinger_bands

def test_calculate_rsi_flat_series():
    """
    Test RSI on a flat series (no price change).
    A flat series should result in RSI = 100.
    """
    series = pd.Series([100.0] * 20)
    rsi = calculate_rsi(series, period=14)
    
    assert pd.isna(rsi.iloc[0:14]).all()
    assert (rsi.iloc[14:] == 100.0).all()

def test_calculate_rsi_increasing_series():
    """
    Test RSI on a strictly increasing series.
    """
    series = pd.Series([float(i) for i in range(100, 120)])
    rsi = calculate_rsi(series, period=14)
    
    assert (rsi.iloc[14:] == 100.0).all()

def test_calculate_bollinger_bands():
    """
    Test BB on a controlled series.
    For a flat series of 100, mean=100, std=0, so upper=100, lower=100.
    """
    series = pd.Series([100.0] * 25)
    upper, lower, mid = calculate_bollinger_bands(series, period=20, std_dev=2.0)
    
    assert pd.isna(upper.iloc[0:19]).all()
    assert (mid.iloc[19:] == 100.0).all()
    assert (upper.iloc[19:] == 100.0).all()
    assert (lower.iloc[19:] == 100.0).all()

def test_calculate_macd_insufficient_data():
    """
    Test MACD handles insufficient data.
    """
    series = pd.Series([100.0] * 10)
    macd, signal, hist = calculate_macd(series)
    
    assert pd.isna(macd).all()
    assert pd.isna(signal).all()
    assert pd.isna(hist).all()
