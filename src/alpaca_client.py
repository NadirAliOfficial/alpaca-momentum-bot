from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient

from .config import Config
from .logger import get_logger


class LiveTradingLocked(Exception):
    """Raised when a live order is attempted while LIVE_TRADING is False."""


class AlpacaClient:
    def __init__(self, config: Config):
        self.config = config
        self.log = get_logger("alpaca", config.log_level)

        # paper=True pins every request to the sandbox host. This is the
        # enforcement point for the LIVE_TRADING flag.
        self.trading = TradingClient(
            api_key=config.api_key,
            secret_key=config.api_secret,
            paper=config.is_paper,
        )
        self.market_data = StockHistoricalDataClient(
            api_key=config.api_key, secret_key=config.api_secret
        )

    def connect(self):
        account = self.trading.get_account()
        mode = "LIVE" if self.config.live_trading else "PAPER"
        self.log.info(
            "Connected to Alpaca [%s] | account=%s status=%s equity=%s buying_power=%s",
            mode,
            account.account_number,
            account.status,
            account.equity,
            account.buying_power,
        )
        if self.config.live_trading:
            self.log.warning("LIVE_TRADING is enabled — real orders will be sent.")
        return account

    def get_account(self):
        return self.trading.get_account()

    def get_clock(self):
        return self.trading.get_clock()

    def is_market_open(self) -> bool:
        return self.trading.get_clock().is_open

    def submit_order(self, order_request):
        if self.config.live_trading:
            self.log.warning("Submitting LIVE order: %s", order_request)
        else:
            self.log.info("Submitting PAPER order: %s", order_request)
        return self.trading.submit_order(order_request)
