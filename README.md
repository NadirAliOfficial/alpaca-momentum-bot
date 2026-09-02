# Alpaca Momentum Bot

Automated trading bot for a 4-hour momentum-breakout strategy
(Keltner Channels + MFI + OBV) on the Alpaca API, with 1% equity risk
sizing and a two-stage position-splitting exit. Long spot positions
only — no options, shorting, or margin.

This repository is delivered in milestones. **Current: Milestone 3.**

## Milestone 1 — Environment, Alpaca integration, safety flag

- Project structure, dependency pinning, Docker deployment scaffold
- Alpaca integration: trading client + historical market-data client
- `LIVE_TRADING` master safety flag (defaults to `False`)
  - When `False`, every Alpaca request is pinned to the paper-trading
    sandbox host and no live order can be placed
  - Must be explicitly set to `True` with real-money keys to trade live
- Rotating file + console logging
- Unit tests for config resolution and the paper/live switch

## Milestone 2 — Indicator layer and entry logic

- `src/indicators.py` — Keltner Channels (20 EMA, 2.0x ATR(20)), Money
  Flow Index (14), On-Balance Volume with its 20 SMA. Pure pandas/numpy,
  no external TA dependency.
- `src/bars.py` — pulls 4-hour OHLCV bars from Alpaca.
- `src/signals.py` — `evaluate_entry(df)` on the last closed bar:
  - **LONG**: close > upper KC, green candle, MFI > 50, OBV > OBV 20 SMA
  - **SHORT**: close < lower KC, red candle, MFI < 50, OBV < OBV 20 SMA
  - **NONE**: otherwise, or when there is not enough history
- `python -m src.main` now scans the watchlist and logs the signal per
  symbol. No orders are placed yet.
- 12 new unit tests: indicator correctness plus long / short / no-signal
  and guard cases for the entry rules.

## Milestone 3 — Risk engine and two-stage exit (simulated)

- `src/risk.py` — `size_position()` caps loss at `RISK_PER_TRADE` (1%)
  of equity given entry and an ATR-based stop; quantity is floored to an
  even lot (min 2) so the scale-out is whole. `atr_stop()` places the
  stop at `STOP_ATR_MULT` x ATR(20) below entry; target is
  `REWARD_RISK` x the per-share risk.
- `src/simulator.py` — `simulate_trade()` walks the bars after entry:
  - **Phase 1**: full position, hard stop + profit target. On the target
    it sells 50% and moves the stop on the runner to breakeven.
  - **Phase 2 (runner)**: exits on the breakeven stop, a 4h close back
    past the Keltner middle, OBV crossing below its SMA, or the Friday
    3:30pm New York cutoff.
  - Returns fills + realised PnL and R multiple. Stop fills before target
    within a bar.
- `python -m src.main` logs the sized plan for any LONG signal.
- 11 new unit tests: sizing math and every exit path.

All execution here is simulated on price data. Live spot order routing
and deployment come in Milestone 4.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Alpaca PAPER keys
```

## Run

```bash
python -m src.main          # connects, prints account + market clock
```

## Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest
```

## Safety

`LIVE_TRADING=False` is the default and is enforced at the client layer
(`TradingClient(paper=True)`). Do not set it to `True` until live
execution has been reviewed and signed off.
