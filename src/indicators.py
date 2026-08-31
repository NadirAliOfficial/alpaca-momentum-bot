import numpy as np
import pandas as pd

KC_LENGTH = 20
KC_ATR_LENGTH = 20
KC_MULTIPLIER = 2.0
MFI_LENGTH = 14
OBV_SMA_LENGTH = 20


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def keltner_channels(
    df: pd.DataFrame,
    length: int = KC_LENGTH,
    atr_length: int = KC_ATR_LENGTH,
    multiplier: float = KC_MULTIPLIER,
) -> pd.DataFrame:
    middle = ema(df["close"], length)
    atr = sma(true_range(df), atr_length)
    return pd.DataFrame(
        {
            "kc_middle": middle,
            "kc_upper": middle + multiplier * atr,
            "kc_lower": middle - multiplier * atr,
        }
    )


def money_flow_index(df: pd.DataFrame, length: int = MFI_LENGTH) -> pd.Series:
    typical = (df["high"] + df["low"] + df["close"]) / 3
    raw_flow = typical * df["volume"]
    delta = typical.diff()
    pos = raw_flow.where(delta > 0, 0.0).rolling(length).sum()
    neg = raw_flow.where(delta < 0, 0.0).rolling(length).sum()
    ratio = pos / neg
    mfi = 100 - (100 / (1 + ratio))
    mfi = mfi.where(neg != 0, 100.0)
    mfi = mfi.where((pos + neg) != 0, 50.0)
    return mfi


def on_balance_volume(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff().fillna(0.0))
    return (direction * df["volume"]).cumsum()


def obv_with_sma(df: pd.DataFrame, sma_length: int = OBV_SMA_LENGTH) -> pd.DataFrame:
    obv = on_balance_volume(df)
    return pd.DataFrame({"obv": obv, "obv_sma": sma(obv, sma_length)})
