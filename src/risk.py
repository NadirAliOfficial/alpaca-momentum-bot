import math
from dataclasses import dataclass

MIN_QUANTITY = 2  # two-stage exit needs an even lot of at least 2


@dataclass
class PositionPlan:
    symbol: str
    entry: float
    stop: float
    target: float
    quantity: int
    risk_amount: float

    @property
    def per_share_risk(self) -> float:
        return self.entry - self.stop

    @property
    def total_risk(self) -> float:
        return self.per_share_risk * self.quantity

    @property
    def reward_risk(self) -> float:
        r = self.per_share_risk
        return (self.target - self.entry) / r if r else 0.0

    @property
    def tradeable(self) -> bool:
        return self.quantity >= MIN_QUANTITY


def atr_stop(entry: float, atr_value: float, mult: float = 1.5) -> float:
    return entry - atr_value * mult


def _even_floor(x: float) -> int:
    n = int(math.floor(x))
    return n - 1 if n % 2 else n


def size_position(
    equity: float,
    risk_per_trade: float,
    entry: float,
    stop: float,
    reward_risk: float = 2.5,
    symbol: str = "",
) -> PositionPlan:
    """1% (configurable) equity risk sizing for a long spot position.

    Quantity is floored to an even lot so the phase-1 scale-out is a whole
    number. Below the 2-share minimum the plan is returned untradeable
    (quantity 0) rather than raising.
    """
    if entry <= stop:
        raise ValueError("stop must be below entry for a long position")

    risk_amount = equity * risk_per_trade
    per_share_risk = entry - stop
    quantity = _even_floor(risk_amount / per_share_risk)
    if quantity < MIN_QUANTITY:
        quantity = 0
    target = entry + per_share_risk * reward_risk
    return PositionPlan(symbol, entry, stop, target, quantity, risk_amount)
