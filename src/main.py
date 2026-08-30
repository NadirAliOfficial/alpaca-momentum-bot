from .alpaca_client import AlpacaClient
from .config import ConfigError, load_config
from .logger import get_logger


def main() -> int:
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Config error: {exc}")
        return 1

    log = get_logger("bot", config.log_level)
    log.info(
        "Starting bot | mode=%s | watchlist=%s | timeframe=%dh | risk=%.2f%%",
        "LIVE" if config.live_trading else "PAPER",
        ",".join(config.watchlist),
        config.bar_timeframe_hours,
        config.risk_per_trade * 100,
    )

    client = AlpacaClient(config)
    account = client.connect()
    clock = client.get_clock()
    log.info("Market open: %s | next open: %s | next close: %s",
             clock.is_open, clock.next_open, clock.next_close)

    log.info("M1 environment check complete. Account equity: %s", account.equity)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
