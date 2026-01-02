from __future__ import annotations

from typing import Any, Dict, Optional

from pybit.unified_trading import HTTP

from .base import ExchangeAdapter, ExchangeError


class BybitExchange(ExchangeAdapter):
    def __init__(self, api_key: Optional[str], api_secret: Optional[str]):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client: Optional[HTTP] = None
        if api_key and api_secret:
            self.client = HTTP(api_key=api_key, api_secret=api_secret)

    def _require_client(self):
        if not self.client:
            raise ExchangeError("Bybit credentials are missing")

    def create_market_buy(self, symbol: str, qty: str) -> Dict[str, Any]:
        self._require_client()
        try:
            return self.client.place_order(
                category="spot", symbol=symbol, side="Buy", orderType="Market", qty=qty
            )
        except Exception as exc:
            raise ExchangeError(f"Bybit buy failed: {exc}") from exc

    def create_market_sell(self, symbol: str, qty: str) -> Dict[str, Any]:
        self._require_client()
        try:
            return self.client.place_order(
                category="spot", symbol=symbol, side="Sell", orderType="Market", qty=qty
            )
        except Exception as exc:
            raise ExchangeError(f"Bybit sell failed: {exc}") from exc
