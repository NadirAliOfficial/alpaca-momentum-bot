import numpy as np
import pandas as pd
import pytest

from src.risk import PositionPlan
from src.simulator import ExitReason, _past_friday_cutoff, simulate_trade


def _prefix(n=32, start=90.0, end=100.0):
    closes = np.linspace(start, end, n)
    rows = []
    prev = closes[0]
    for c in closes:
        o = prev
        rows.append((o, max(o, c) + 0.2, min(o, c) - 0.2, c, 1000.0))
        prev = c
    return rows


def _df(post_rows, freq="4h", start="2025-01-06 09:30"):
    rows = _prefix() + post_rows
    idx = pd.date_range(start=start, periods=len(rows), freq=freq)
    return pd.DataFrame(
        rows, columns=["open", "high", "low", "close", "volume"], index=idx
    )


def _plan(qty=10):
    # entry 100, stop 98, target 105 (reward:risk 2.5)
    return PositionPlan("SPY", entry=100.0, stop=98.0, target=105.0,
                        quantity=qty, risk_amount=200.0)


ENTRY = 31  # last bar of the 32-row prefix


def test_phase1_stop_loss():
    df = _df([(100.0, 100.5, 96.0, 97.0, 1000.0)])
    res = simulate_trade(df, _plan(), ENTRY)
    assert [f.reason for f in res.fills] == [ExitReason.STOP]
    assert res.fills[0].quantity == 10
    assert res.pnl == pytest.approx(-20.0)
    assert res.r_multiple == pytest.approx(-1.0)


def test_scale_out_then_breakeven_stop():
    df = _df([
        (100.0, 106.0, 101.0, 105.0, 1000.0),   # hits target -> scale 5 @ 105
        (104.0, 104.5, 99.0, 100.0, 1000.0),    # runner hits breakeven (100)
    ])
    res = simulate_trade(df, _plan(), ENTRY)
    assert [f.reason for f in res.fills] == [
        ExitReason.TARGET_SCALE, ExitReason.BREAKEVEN,
    ]
    assert res.reached_phase2 is True
    assert res.fills[0].quantity == 5 and res.fills[1].quantity == 5
    assert res.pnl == pytest.approx(25.0)      # 5*(105-100) + 5*(100-100)


def test_scale_out_then_friday_cutoff():
    # place the runner bar on a Friday after 15:30 New York
    idx_rows = _prefix() + [
        (100.0, 106.0, 101.0, 105.0, 1000.0),
        (104.0, 104.9, 101.0, 103.0, 1000.0),
    ]
    idx = list(pd.date_range("2025-01-06 09:30", periods=len(idx_rows) - 1, freq="4h"))
    idx.append(pd.Timestamp("2025-01-10 15:30"))   # Friday
    df = pd.DataFrame(idx_rows, columns=["open", "high", "low", "close", "volume"],
                      index=pd.DatetimeIndex(idx))
    res = simulate_trade(df, _plan(), ENTRY)
    assert [f.reason for f in res.fills] == [
        ExitReason.TARGET_SCALE, ExitReason.FRIDAY,
    ]
    assert res.pnl == pytest.approx(40.0)          # 5*(105-100) + 5*(103-100)


def test_scale_out_then_kc_center_cross():
    df = _df([
        (100.0, 106.0, 101.0, 105.0, 1000.0),   # target -> scale, stop to breakeven
        (105.0, 113.0, 104.0, 112.0, 1000.0),    # runner rides up
        (112.0, 117.0, 111.0, 116.0, 1000.0),
        (116.0, 117.0, 112.0, 116.0, 1000.0),
        (114.0, 116.0, 100.5, 102.0, 1000.0),    # closes back below the KC middle
    ])
    res = simulate_trade(df, _plan(), ENTRY)
    assert [f.reason for f in res.fills] == [
        ExitReason.TARGET_SCALE, ExitReason.KC_REVERT,
    ]
    assert res.pnl == pytest.approx(35.0)      # 5*(105-100) + 5*(102-100)


def test_scale_out_then_obv_cross_down():
    df = _df([
        (100.0, 106.0, 101.0, 105.0, 1000.0),        # target -> scale
        (100.5, 101.0, 100.2, 100.3, 30_000.0),      # heavy down-volume, OBV < OBV_SMA
    ])
    res = simulate_trade(df, _plan(), ENTRY)
    assert [f.reason for f in res.fills] == [
        ExitReason.TARGET_SCALE, ExitReason.OBV_CROSS,
    ]


def test_no_exit_runs_to_end_of_data():
    df = _df([(100.0, 100.4, 99.5, 100.2, 1000.0)])   # drifts, never hits stop/target
    res = simulate_trade(df, _plan(), ENTRY)
    assert res.fills[-1].reason is ExitReason.END
    assert res.fills[-1].quantity == 10


def test_friday_cutoff_helper_tz_aware():
    # 2025-01-10 is a Friday; 20:30 UTC == 15:30 New York (EST)
    assert _past_friday_cutoff(pd.Timestamp("2025-01-10 20:30", tz="UTC")) is True
    assert _past_friday_cutoff(pd.Timestamp("2025-01-10 20:29", tz="UTC")) is False
    assert _past_friday_cutoff(pd.Timestamp("2025-01-09 20:30", tz="UTC")) is False
