from dataclasses import dataclass, field
from enum import Enum

import pandas as pd

from .risk import PositionPlan
from .signals import compute_features

NY_TZ = "America/New_York"
FRIDAY = 4
CUTOFF = (15, 30)  # 3:30 PM New York time


class ExitReason(str, Enum):
    STOP = "stop_loss"
    TARGET_SCALE = "target_scale_out"
    BREAKEVEN = "breakeven_stop"
    KC_REVERT = "kc_center_cross"
    OBV_CROSS = "obv_cross_down"
    FRIDAY = "friday_cutoff"
    END = "end_of_data"


@dataclass
class Fill:
    timestamp: object
    price: float
    quantity: int
    reason: ExitReason


@dataclass
class TradeResult:
    plan: PositionPlan
    fills: list = field(default_factory=list)

    @property
    def pnl(self) -> float:
        return sum((f.price - self.plan.entry) * f.quantity for f in self.fills)

    @property
    def r_multiple(self) -> float:
        risk = self.plan.total_risk
        return self.pnl / risk if risk else 0.0

    @property
    def reached_phase2(self) -> bool:
        return any(f.reason is ExitReason.TARGET_SCALE for f in self.fills)


def _past_friday_cutoff(ts) -> bool:
    ts = pd.Timestamp(ts)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(NY_TZ)
    return ts.weekday() == FRIDAY and (ts.hour, ts.minute) >= CUTOFF


def simulate_trade(
    df: pd.DataFrame,
    plan: PositionPlan,
    entry_index: int,
    scale_out: float = 0.5,
) -> TradeResult:
    """Walk the bars after `entry_index` and apply the two-stage exit.

    Phase 1: full position with a hard stop and a profit target. When the
    target trades, `scale_out` of the position is sold and the stop on the
    runner moves to breakeven (phase 2).
    Phase 2: runner exits on the breakeven stop, a 4h close back past the
    Keltner middle, OBV crossing below its SMA, or the Friday 3:30pm cutoff.
    Within a bar a stop is assumed to fill before a target.
    """
    feats = compute_features(df)
    result = TradeResult(plan=plan)

    remaining = plan.quantity
    stop = plan.stop
    phase = 1

    for i in range(entry_index + 1, len(feats)):
        row = feats.iloc[i]
        ts = feats.index[i]

        if _past_friday_cutoff(ts):
            result.fills.append(Fill(ts, float(row["close"]), remaining, ExitReason.FRIDAY))
            return result

        if row["low"] <= stop:
            reason = ExitReason.STOP if phase == 1 else ExitReason.BREAKEVEN
            result.fills.append(Fill(ts, stop, remaining, reason))
            return result

        if phase == 1:
            if row["high"] >= plan.target:
                scaled = int(remaining * scale_out)
                if scaled >= 1:
                    result.fills.append(
                        Fill(ts, plan.target, scaled, ExitReason.TARGET_SCALE)
                    )
                    remaining -= scaled
                stop = plan.entry
                phase = 2
            continue

        if row["close"] < row["kc_middle"]:
            result.fills.append(Fill(ts, float(row["close"]), remaining, ExitReason.KC_REVERT))
            return result
        if row["obv"] < row["obv_sma"]:
            result.fills.append(Fill(ts, float(row["close"]), remaining, ExitReason.OBV_CROSS))
            return result

    last = feats.iloc[-1]
    result.fills.append(Fill(feats.index[-1], float(last["close"]), remaining, ExitReason.END))
    return result
