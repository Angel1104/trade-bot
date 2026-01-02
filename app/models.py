from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class WebhookPayload(BaseModel):
    passphrase: str
    symbol: str
    action: Literal["BUY", "CLOSE"]
    qty: Decimal
    type: str = Field("MARKET")
    ts: Optional[int] = None
    event_id: Optional[str] = None
    strategy: Optional[str] = None

    model_config = {"extra": "ignore"}

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v
