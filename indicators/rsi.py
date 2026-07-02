"""
Relative Strength Index (RSI) computation.
"""
import pandas as pd
import numpy as np

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI for a given price series using Wilder's Smoothing.
    """
    if len(series) < period + 1:
        return pd.Series(np.nan, index=series.index)
        
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    
    # Wilder's Smoothing (alpha = 1/period)
    roll_up = up.ewm(alpha=1/period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, adjust=False).mean()
    
    # Handle division by zero
    rs = roll_up / roll_down.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # If roll_down is 0, RSI should be 100
    rsi[roll_down == 0] = 100.0
    
    # Set the first 'period' rows to NaN
    rsi.iloc[:period] = np.nan
    
    return rsi
