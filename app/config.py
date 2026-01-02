from __future__ import annotations

import json
from functools import lru_cache
from typing import Dict, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field("tv-webhook-backend", env="APP_NAME")
    tv_passphrase: str = Field(..., env="TV_PASSPHRASE")
    tv_webhook_hmac_secret: Optional[str] = Field(None, env="TV_WEBHOOK_HMAC_SECRET")

    exchange_default: Literal["binance", "bybit"] = Field("binance", env="EXCHANGE_DEFAULT")
    exchange_symbol_map: Dict[str, Literal["binance", "bybit"]] = Field(
        default_factory=dict, env="EXCHANGE_SYMBOL_MAP"
    )

    dry_run: bool = Field(True, env="DRY_RUN")

    binance_api_key: Optional[str] = Field(None, env="BINANCE_API_KEY")
    binance_api_secret: Optional[str] = Field(None, env="BINANCE_API_SECRET")

    bybit_api_key: Optional[str] = Field(None, env="BYBIT_API_KEY")
    bybit_api_secret: Optional[str] = Field(None, env="BYBIT_API_SECRET")

    idempotency_ttl_seconds: int = Field(60, env="IDEMPOTENCY_TTL_SECONDS")
    idempotency_cache_size: int = Field(512, env="IDEMPOTENCY_CACHE_SIZE")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("exchange_symbol_map", mode="before")
    @classmethod
    def parse_symbol_map(cls, v):
        if not v:
            return {}
        if isinstance(v, dict):
            parsed = v
        else:
            try:
                parsed = json.loads(v)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid EXCHANGE_SYMBOL_MAP: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("EXCHANGE_SYMBOL_MAP must be a JSON object")
        for symbol, exch in parsed.items():
            if exch not in {"binance", "bybit"}:
                raise ValueError(f"Unsupported exchange '{exch}' for symbol '{symbol}'")
        return parsed


@lru_cache()
def get_settings() -> Settings:
    return Settings()
