import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
LIVE_BASE_URL = "https://api.alpaca.markets"


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _get_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


class ConfigError(Exception):
    pass


@dataclass
class Config:
    api_key: str
    api_secret: str
    live_trading: bool
    watchlist: list[str] = field(default_factory=list)
    bar_timeframe_hours: int = 4
    risk_per_trade: float = 0.01
    stop_atr_mult: float = 1.5
    reward_risk: float = 2.5
    log_level: str = "INFO"

    @property
    def is_paper(self) -> bool:
        return not self.live_trading

    @property
    def base_url(self) -> str:
        return LIVE_BASE_URL if self.live_trading else PAPER_BASE_URL

    def validate(self) -> None:
        if not self.api_key or not self.api_secret:
            raise ConfigError(
                "ALPACA_API_KEY and ALPACA_API_SECRET must be set (see .env.example)."
            )
        if self.bar_timeframe_hours <= 0:
            raise ConfigError("BAR_TIMEFRAME_HOURS must be positive.")
        if not 0 < self.risk_per_trade < 1:
            raise ConfigError("RISK_PER_TRADE must be between 0 and 1.")
        if self.stop_atr_mult <= 0:
            raise ConfigError("STOP_ATR_MULT must be positive.")
        if self.reward_risk <= 0:
            raise ConfigError("REWARD_RISK must be positive.")


def load_config() -> Config:
    cfg = Config(
        api_key=os.getenv("ALPACA_API_KEY", ""),
        api_secret=os.getenv("ALPACA_API_SECRET", ""),
        live_trading=_get_bool("LIVE_TRADING", False),
        watchlist=_get_list("WATCHLIST", ["SPY"]),
        bar_timeframe_hours=int(os.getenv("BAR_TIMEFRAME_HOURS", "4")),
        risk_per_trade=float(os.getenv("RISK_PER_TRADE", "0.01")),
        stop_atr_mult=float(os.getenv("STOP_ATR_MULT", "1.5")),
        reward_risk=float(os.getenv("REWARD_RISK", "2.5")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
    cfg.validate()
    return cfg
