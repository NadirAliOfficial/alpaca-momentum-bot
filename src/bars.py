from datetime import datetime, timedelta, timezone

import pandas as pd
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from .alpaca_client import AlpacaClient

_COLUMNS = ["open", "high", "low", "close", "volume"]


def get_bars(
    client: AlpacaClient,
    symbol: str,
    hours: int = 4,
    lookback_days: int = 60,
) -> pd.DataFrame:
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame(hours, TimeFrameUnit.Hour),
        start=datetime.now(timezone.utc) - timedelta(days=lookback_days),
    )
    df = client.market_data.get_stock_bars(request).df
    if df.empty:
        return df

    df = df.reset_index()
    if "symbol" in df.columns:
        df = df.drop(columns=["symbol"])
    df = df.set_index("timestamp")
    return df[_COLUMNS]
