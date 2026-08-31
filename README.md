# Alpaca Momentum Bot

Automated trading bot for a 4-hour momentum-breakout strategy
(Keltner Channels + MFI + OBV) on the Alpaca API, with ATM weekly
contract selection and a two-stage position-splitting exit matrix.

This repository is delivered in milestones. **Current: Milestone 2.**

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

Later milestones add the risk engine with the two-stage exit and live
contract-chain execution.

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
