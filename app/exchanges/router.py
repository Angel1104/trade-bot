from __future__ import annotations

from typing import Dict, Tuple

from ..config import Settings
from .base import ExchangeAdapter, ExchangeError
from .binance import BinanceExchange
from .bybit import BybitExchange


class ExchangeRouter:
    def __init__(self, settings: Settings):
        self.default = settings.exchange_default
        self.symbol_map: Dict[str, str] = {
            k.upper(): v for k, v in (settings.exchange_symbol_map or {}).items()
        }
        self.adapters: Dict[str, ExchangeAdapter] = {
            "binance": BinanceExchange(settings.binance_api_key, settings.binance_api_secret),
            "bybit": BybitExchange(settings.bybit_api_key, settings.bybit_api_secret),
        }

    def resolve_exchange_name(self, symbol: str) -> str:
        sym = symbol.upper()
        if sym in self.symbol_map:
            return self.symbol_map[sym]
        return self.default

    def get_exchange(self, symbol: str) -> Tuple[str, ExchangeAdapter]:
        name = self.resolve_exchange_name(symbol)
        adapter = self.adapters.get(name)
        if not adapter:
            raise ExchangeError(f"Exchange adapter '{name}' not available")
        return name, adapter
