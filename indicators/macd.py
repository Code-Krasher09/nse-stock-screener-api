"""
Moving Average Convergence Divergence (MACD) computation.
"""
import pandas as pd
import numpy as np

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD for a given price series.
    Returns a tuple of (macd_line, signal_line, macd_histogram)
    """
    if len(series) < slow:
        nan_series = pd.Series(np.nan, index=series.index)
        return nan_series, nan_series, nan_series

    # Calculate EMAs
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    
    # MACD Line
    macd_line = ema_fast - ema_slow
    
    # Signal Line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # MACD Histogram
    macd_hist = macd_line - signal_line
    
    return macd_line, signal_line, macd_hist
