import importlib

import pytest
from fastapi.testclient import TestClient

import app.config as config
from app.exchanges.base import ExchangeError


def _reload_app(monkeypatch, dry_run: bool = True):
    # Configure environment for the test run
    monkeypatch.setenv("TV_PASSPHRASE", "secret")
    monkeypatch.setenv("EXCHANGE_DEFAULT", "binance")
    monkeypatch.setenv("DRY_RUN", "true" if dry_run else "false")
    monkeypatch.delenv("EXCHANGE_SYMBOL_MAP", raising=False)

    # Reload settings and app to pick up env changes
    importlib.reload(config)
    config.get_settings.cache_clear()
    import app.main as main  # noqa: WPS433

    importlib.reload(main)
    return main


def _payload():
    return {
        "passphrase": "secret",
        "symbol": "BTCUSDT",
        "action": "BUY",
        "qty": "0.001",
        "type": "MARKET",
        "event_id": "test-event-1",
    }


def test_webhook_dry_run_skips_exchange(monkeypatch):
    main = _reload_app(monkeypatch, dry_run=True)

    class DummyAdapter:
        def __init__(self):
            self.called = False

        def create_market_buy(self, symbol, qty):
            self.called = True
            return {"ok": True}

        def create_market_sell(self, symbol, qty):
            self.called = True
            return {"ok": True}

    dummy = DummyAdapter()
    monkeypatch.setattr(main.exchange_router, "get_exchange", lambda symbol: ("binance", dummy))

    client = TestClient(main.app)
    resp = client.post("/webhook", json=_payload())

    assert resp.status_code == 200
    assert resp.json().get("dry_run") is True
    assert dummy.called is False  # no calls when dry-run


def test_webhook_read_only_key_returns_error(monkeypatch):
    main = _reload_app(monkeypatch, dry_run=False)

    class FailingAdapter:
        def create_market_buy(self, symbol, qty):
            raise ExchangeError("read-only key cannot trade")

        def create_market_sell(self, symbol, qty):
            raise ExchangeError("read-only key cannot trade")

    monkeypatch.setattr(main.exchange_router, "get_exchange", lambda symbol: ("binance", FailingAdapter()))

    client = TestClient(main.app)
    resp = client.post("/webhook", json=_payload())

    assert resp.status_code == 500
    assert resp.json().get("detail") == "Exchange order failed"
