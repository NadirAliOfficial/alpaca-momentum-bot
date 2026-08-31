import numpy as np
import pandas as pd
import pytest

from src.indicators import (
    ema,
    keltner_channels,
    money_flow_index,
    obv_with_sma,
    on_balance_volume,
    true_range,
)


def _df(closes, volume=1000.0):
    closes = pd.Series(closes, dtype=float)
    opens = closes.shift(1).fillna(closes.iloc[0])
    highs = pd.concat([opens, closes], axis=1).max(axis=1) + 0.1
    lows = pd.concat([opens, closes], axis=1).min(axis=1) - 0.1
    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volume}
    )


def test_true_range_matches_manual():
    df = _df([10, 12, 11, 15])
    tr = true_range(df)
    # bar 0 has no prior close; only high-low is defined
    assert tr.iloc[0] == pytest.approx(0.2)
    # bar 1: high=12.1, low=9.9, prev_close=10 -> max(2.2, 2.1, 0.1)
    assert tr.iloc[1] == pytest.approx(2.2)


def test_ema_seed_equals_first_value():
    s = pd.Series([5.0, 5.0, 5.0])
    assert ema(s, 3).iloc[0] == 5.0


def test_keltner_bands_bracket_middle():
    df = _df(list(np.linspace(100, 110, 40)))
    kc = keltner_channels(df)
    last = kc.iloc[-1]
    assert last["kc_lower"] < last["kc_middle"] < last["kc_upper"]
    assert np.isnan(kc["kc_upper"].iloc[0])


def test_mfi_bounds_and_direction():
    up = money_flow_index(_df(list(np.linspace(100, 130, 30))))
    down = money_flow_index(_df(list(np.linspace(130, 100, 30))))
    assert 0 <= up.iloc[-1] <= 100
    assert up.iloc[-1] > 50
    assert down.iloc[-1] < 50


def test_obv_tracks_direction():
    up = on_balance_volume(_df([10, 11, 12, 13, 14]))
    assert up.iloc[-1] == 4000.0  # first diff is 0, then +1000 x4
    down = on_balance_volume(_df([14, 13, 12, 11, 10]))
    assert down.iloc[-1] == -4000.0


def test_obv_sma_column_present():
    out = obv_with_sma(_df(list(np.linspace(100, 120, 40))))
    assert set(out.columns) == {"obv", "obv_sma"}
    assert out["obv"].iloc[-1] > out["obv_sma"].iloc[-1]
