import numpy as np
import pandas as pd

from src.signals import SignalType, compute_features, evaluate_entry


def _df(closes, volume=1000.0):
    closes = pd.Series(closes, dtype=float)
    opens = closes.shift(1).fillna(closes.iloc[0])
    highs = pd.concat([opens, closes], axis=1).max(axis=1) + 0.1
    lows = pd.concat([opens, closes], axis=1).min(axis=1) - 0.1
    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volume}
    )


def test_long_signal_on_upper_break_with_confirmations():
    closes = list(np.linspace(100, 104, 40)) + [112.0]
    sig = evaluate_entry(_df(closes), "SPY")
    assert sig.type is SignalType.LONG
    assert sig.symbol == "SPY"
    assert sig.price == 112.0


def test_short_signal_on_lower_break_with_confirmations():
    closes = list(np.linspace(110, 106, 40)) + [98.0]
    sig = evaluate_entry(_df(closes), "QQQ")
    assert sig.type is SignalType.SHORT
    assert sig.price == 98.0


def test_no_signal_when_range_bound():
    closes = [100.0] * 40
    sig = evaluate_entry(_df(closes), "AAPL")
    assert sig.type is SignalType.NONE
    assert sig.reason == "no entry conditions met"


def test_no_signal_when_break_but_wrong_candle_color():
    # breaks the upper band on the last bar, but the bar is red (close < open)
    closes = list(np.linspace(100, 104, 40)) + [112.0]
    df = _df(closes)
    df.iloc[-1, df.columns.get_loc("open")] = 130.0  # force red
    sig = evaluate_entry(df, "SPY")
    assert sig.type is SignalType.NONE


def test_insufficient_history_returns_none():
    sig = evaluate_entry(_df([100, 101, 102, 103, 104]), "SPY")
    assert sig.type is SignalType.NONE
    assert sig.reason == "insufficient history"


def test_compute_features_adds_all_columns():
    feats = compute_features(_df(list(np.linspace(100, 120, 40))))
    for col in ("kc_middle", "kc_upper", "kc_lower", "obv", "obv_sma", "mfi"):
        assert col in feats.columns
