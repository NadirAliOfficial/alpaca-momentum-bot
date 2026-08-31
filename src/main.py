from .alpaca_client import AlpacaClient
from .bars import get_bars
from .config import ConfigError, load_config
from .logger import get_logger
from .signals import evaluate_entry


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

    log.info("Account equity: %s", account.equity)

    for symbol in config.watchlist:
        df = get_bars(client, symbol, hours=config.bar_timeframe_hours)
        if df.empty:
            log.warning("%s | no bar data returned", symbol)
            continue
        sig = evaluate_entry(df, symbol)
        log.info(
            "%s | bars=%d last_close=%.2f | signal=%s (%s)",
            symbol, len(df), sig.price, sig.type.value, sig.reason,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
