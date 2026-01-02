from __future__ import annotations

from typing import Protocol


class ExchangeError(Exception):
    pass


class ExchangeAdapter(Protocol):
    def create_market_buy(self, symbol: str, qty: str):
        ...

    def create_market_sell(self, symbol: str, qty: str):
        ...
