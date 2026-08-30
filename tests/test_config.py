import pytest

from src.config import (
    LIVE_BASE_URL,
    PAPER_BASE_URL,
    Config,
    ConfigError,
    _get_bool,
    _get_list,
    load_config,
)


def _base(**kw):
    defaults = dict(api_key="k", api_secret="s", live_trading=False)
    defaults.update(kw)
    return Config(**defaults)


def test_default_is_paper():
    cfg = _base()
    assert cfg.is_paper is True
    assert cfg.base_url == PAPER_BASE_URL


def test_live_flag_switches_endpoint():
    cfg = _base(live_trading=True)
    assert cfg.is_paper is False
    assert cfg.base_url == LIVE_BASE_URL


def test_missing_keys_rejected():
    with pytest.raises(ConfigError):
        _base(api_key="").validate()


def test_bad_risk_rejected():
    with pytest.raises(ConfigError):
        _base(risk_per_trade=1.5).validate()


@pytest.mark.parametrize(
    "raw,expected",
    [("true", True), ("True", True), ("1", True), ("on", True),
     ("false", False), ("0", False), ("", False), ("no", False)],
)
def test_get_bool(monkeypatch, raw, expected):
    monkeypatch.setenv("X_FLAG", raw)
    assert _get_bool("X_FLAG", False) is expected


def test_get_bool_default_when_unset(monkeypatch):
    monkeypatch.delenv("X_FLAG", raising=False)
    assert _get_bool("X_FLAG", True) is True


def test_get_list(monkeypatch):
    monkeypatch.setenv("X_LIST", " spy, qqq ,aapl")
    assert _get_list("X_LIST", []) == ["SPY", "QQQ", "AAPL"]


def test_load_config_defaults_to_paper(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "k")
    monkeypatch.setenv("ALPACA_API_SECRET", "s")
    monkeypatch.delenv("LIVE_TRADING", raising=False)
    cfg = load_config()
    assert cfg.live_trading is False
    assert cfg.is_paper is True
