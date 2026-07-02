import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock
from ingestion.fetcher import get_nifty500_symbols, fetch_and_store_data
from sqlalchemy.ext.asyncio import AsyncSession

def test_get_nifty500_symbols():
    mock_csv = b"Symbol,Company Name\nRELIANCE,Reliance Industries\nTCS,Tata Consultancy Services\n"
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = mock_csv
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        symbols = get_nifty500_symbols()
        assert symbols == ["RELIANCE", "TCS"]

@pytest.mark.asyncio
@patch("ingestion.fetcher.yf.download")
async def test_fetch_and_store_data_empty_symbols(mock_yf_download):
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch("ingestion.fetcher.get_nifty500_symbols", return_value=[]):
        await fetch_and_store_data(mock_session)
        
    mock_yf_download.assert_not_called()
    mock_session.execute.assert_not_called()

@pytest.mark.asyncio
@patch("ingestion.fetcher.yf.download")
async def test_fetch_and_store_data(mock_yf_download):
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Mock yfinance return
    df = pd.DataFrame({
        'Open': [100.0],
        'High': [105.0],
        'Low': [99.0],
        'Close': [104.0],
        'Volume': [1000]
    }, index=pd.to_datetime(['2023-01-01']))
    mock_yf_download.return_value = df
    
    # Mock DB execution
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.symbol = "RELIANCE"
    mock_row.id = 1
    mock_result.all.return_value = [mock_row]
    mock_session.execute.return_value = mock_result
    
    await fetch_and_store_data(mock_session, ["RELIANCE"])
    
    mock_yf_download.assert_called_once()
    assert mock_session.execute.call_count == 3  # Upsert stocks, Select stocks, Upsert prices
    assert mock_session.commit.call_count == 2
