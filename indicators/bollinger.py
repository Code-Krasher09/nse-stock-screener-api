"""
Bollinger Bands computation.
"""
import numpy as np
import pandas as pd


def calculate_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands for a given price series.
    Returns a tuple of (upper_band, lower_band, mid_band)
    """
    if len(series) < period:
        nan_series = pd.Series(np.nan, index=series.index)
        return nan_series, nan_series, nan_series

    # Mid Band (Simple Moving Average)
    mid_band = series.rolling(window=period).mean()

    # Standard Deviation
    std = series.rolling(window=period).std()

    # Upper and Lower Bands
    upper_band = mid_band + (std_dev * std)
    lower_band = mid_band - (std_dev * std)

    return upper_band, lower_band, mid_band

