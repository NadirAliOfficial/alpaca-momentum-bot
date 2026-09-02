"""M3 walk-through: find a historical long trigger, size the position with
1% equity risk, and run the two-stage exit simulator on real Alpaca bars.
"""
from src.alpaca_client import AlpacaClient
from src.config import load_config
from src.bars import get_bars
from src.indicators import atr
from src.risk import atr_stop, size_position
from src.signals import compute_features
from src.simulator import simulate_trade

EQUITY = 100_000
SYMBOL = "SPY"


def main() -> None:
    client = AlpacaClient(load_config())
    df = get_bars(client, SYMBOL, hours=4, lookback_days=250)
    feats = compute_features(df)

    triggers = [
        i
        for i in range(30, len(feats) - 25)
        if feats.iloc[i]["close"] > feats.iloc[i]["kc_upper"]
        and feats.iloc[i]["close"] > feats.iloc[i]["open"]
        and feats.iloc[i]["mfi"] > 50
        and feats.iloc[i]["obv"] > feats.iloc[i]["obv_sma"]
    ]
    if not triggers:
        print("no long trigger in the sample window")
        return

    def build(i):
        entry = float(feats["close"].iloc[i])
        stop = atr_stop(entry, float(atr(df).iloc[i]), 1.5)
        plan = size_position(EQUITY, 0.01, entry, stop, 2.5, SYMBOL)
        return plan, simulate_trade(df.iloc[: i + 25], plan, i)

    # prefer a trigger that actually runs the two-stage exit
    entry_idx = triggers[0]
    plan, res = build(entry_idx)
    for i in triggers:
        p, r = build(i)
        if r.reached_phase2:
            entry_idx, plan, res = i, p, r
            break

    print(f"entry bar : {feats.index[entry_idx]}  close={plan.entry:.2f}")
    print(
        f"PLAN      : qty={plan.quantity}  entry={plan.entry:.2f}  "
        f"stop={plan.stop:.2f}  target={plan.target:.2f}  "
        f"risk=${plan.total_risk:.2f}  R:R={plan.reward_risk:.1f}"
    )
    for f in res.fills:
        print(f"  fill    : {f.timestamp}  qty={f.quantity} @ {f.price:.2f}  [{f.reason.value}]")
    print(f"result    : PnL=${res.pnl:.2f}  R={res.r_multiple:.2f}")


if __name__ == "__main__":
    main()
