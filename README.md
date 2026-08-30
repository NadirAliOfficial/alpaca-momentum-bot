# Alpaca Options Momentum Bot

Automated options trading bot for a 4-hour momentum-breakout strategy
(Keltner Channels + MFI + OBV) using the Alpaca API. Buys ATM weekly
contracts with a two-stage position-splitting exit matrix.

This repository is delivered in milestones. **Current: Milestone 1.**

## Milestone 1 — Environment, Alpaca integration, safety flag

- Project structure, dependency pinning, Docker deployment scaffold
- Alpaca integration: trading client + stock and option historical data clients
- `LIVE_TRADING` master safety flag (defaults to `False`)
  - When `False`, every Alpaca request is pinned to the paper-trading
    sandbox host and no live order can be placed
  - Must be explicitly set to `True` with real-money keys to trade live
- Rotating file + console logging
- Unit tests for config resolution and the paper/live switch

Later milestones add the indicator layer (`pandas-ta`), entry logic, the
risk engine with the two-stage exit, and live options-chain execution.

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
