from dataclasses import dataclass
from enum import Enum

import pandas as pd

from .indicators import keltner_channels, money_flow_index, obv_with_sma

MFI_LONG_THRESHOLD = 50
MFI_SHORT_THRESHOLD = 50


class SignalType(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


@dataclass
class Signal:
    type: SignalType
    symbol: str
    price: float
    reason: str


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    kc = keltner_channels(df)
    obv = obv_with_sma(df)
    return df.join([kc, obv]).assign(mfi=money_flow_index(df))


def evaluate_entry(df: pd.DataFrame, symbol: str = "") -> Signal:
    feats = compute_features(df)
    row = feats.iloc[-1]
    price = float(row["close"])

    if row[["kc_upper", "kc_lower", "obv_sma", "mfi"]].isna().any():
        return Signal(SignalType.NONE, symbol, price, "insufficient history")

    green = row["close"] > row["open"]
    red = row["close"] < row["open"]

    long_ok = (
        row["close"] > row["kc_upper"]
        and green
        and row["mfi"] > MFI_LONG_THRESHOLD
        and row["obv"] > row["obv_sma"]
    )
    short_ok = (
        row["close"] < row["kc_lower"]
        and red
        and row["mfi"] < MFI_SHORT_THRESHOLD
        and row["obv"] < row["obv_sma"]
    )

    if long_ok:
        return Signal(
            SignalType.LONG, symbol, price,
            "close>KC_upper, green candle, MFI>50, OBV>OBV_SMA",
        )
    if short_ok:
        return Signal(
            SignalType.SHORT, symbol, price,
            "close<KC_lower, red candle, MFI<50, OBV<OBV_SMA",
        )
    return Signal(SignalType.NONE, symbol, price, "no entry conditions met")
