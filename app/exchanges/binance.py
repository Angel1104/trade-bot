from __future__ import annotations

from typing import Any, Dict, Optional

from binance.spot import Spot

from .base import ExchangeAdapter, ExchangeError


class BinanceExchange(ExchangeAdapter):
    def __init__(self, api_key: Optional[str], api_secret: Optional[str]):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client: Optional[Spot] = None
        if api_key and api_secret:
            self.client = Spot(api_key=api_key, api_secret=api_secret)

    def _require_client(self):
        if not self.client:
            raise ExchangeError("Binance credentials are missing")

    def create_market_buy(self, symbol: str, qty: str) -> Dict[str, Any]:
        self._require_client()
        try:
            return self.client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=qty)
        except Exception as exc:
            raise ExchangeError(f"Binance buy failed: {exc}") from exc

    def create_market_sell(self, symbol: str, qty: str) -> Dict[str, Any]:
        self._require_client()
        try:
            return self.client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=qty)
        except Exception as exc:
            raise ExchangeError(f"Binance sell failed: {exc}") from exc
