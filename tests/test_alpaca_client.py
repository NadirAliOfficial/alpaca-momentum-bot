from unittest.mock import MagicMock, patch

from src.config import Config


def _cfg(live=False):
    return Config(api_key="k", api_secret="s", live_trading=live)


@patch("src.alpaca_client.OptionHistoricalDataClient")
@patch("src.alpaca_client.StockHistoricalDataClient")
@patch("src.alpaca_client.TradingClient")
def test_paper_mode_pins_sandbox(trading_cls, _stock, _opt):
    from src.alpaca_client import AlpacaClient

    AlpacaClient(_cfg(live=False))
    assert trading_cls.call_args.kwargs["paper"] is True


@patch("src.alpaca_client.OptionHistoricalDataClient")
@patch("src.alpaca_client.StockHistoricalDataClient")
@patch("src.alpaca_client.TradingClient")
def test_live_mode_uses_live_endpoint(trading_cls, _stock, _opt):
    from src.alpaca_client import AlpacaClient

    AlpacaClient(_cfg(live=True))
    assert trading_cls.call_args.kwargs["paper"] is False


@patch("src.alpaca_client.OptionHistoricalDataClient")
@patch("src.alpaca_client.StockHistoricalDataClient")
@patch("src.alpaca_client.TradingClient")
def test_submit_order_delegates(trading_cls, _stock, _opt):
    from src.alpaca_client import AlpacaClient

    instance = MagicMock()
    trading_cls.return_value = instance
    client = AlpacaClient(_cfg(live=False))
    req = {"symbol": "SPY"}
    client.submit_order(req)
    instance.submit_order.assert_called_once_with(req)
