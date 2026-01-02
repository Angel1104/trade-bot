from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .config import Settings, get_settings
from .exchanges.base import ExchangeError
from .exchanges.router import ExchangeRouter
from .idempotency import IdempotencyStore, build_idempotency_key
from .logging import configure_logging, request_id_ctx_var
from .models import WebhookPayload

settings: Settings = get_settings()
configure_logging()

logger = logging.getLogger("webhook")
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

exchange_router = ExchangeRouter(settings)
idempotency_store = IdempotencyStore(
    ttl_seconds=settings.idempotency_ttl_seconds, maxsize=settings.idempotency_cache_size
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    token = request_id_ctx_var.set(request_id)
    request.state.request_id = request_id
    start = time.time()
    try:
        response = await call_next(request)
    finally:
        request_id_ctx_var.reset(token)
    duration_ms = int((time.time() - start) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-ms"] = str(duration_ms)
    return response


def verify_hmac(raw_body: bytes, provided_signature: str) -> None:
    if not settings.tv_webhook_hmac_secret:
        return
    if not provided_signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    expected = hmac.new(
        key=settings.tv_webhook_hmac_secret.encode(), msg=raw_body, digestmod=hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected.lower(), provided_signature.lower()):
        raise HTTPException(status_code=401, detail="Invalid signature")


@app.get("/health")
async def health() -> Dict[str, bool]:
    return {"ok": True}


@app.get("/version")
async def version() -> Dict[str, str]:
    return {"version": "0.1.0"}


@app.post("/webhook")
async def handle_webhook(request: Request):
    raw_body = await request.body()
    verify_hmac(raw_body, request.headers.get("X-Signature"))

    try:
        payload_dict = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        payload = WebhookPayload(**payload_dict)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    if payload.passphrase != settings.tv_passphrase:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if payload.type.upper() != "MARKET":
        raise HTTPException(status_code=400, detail="Only MARKET orders supported")

    if payload.action == "CLOSE" and payload.qty is None:
        raise HTTPException(status_code=400, detail="qty is required for CLOSE action")

    exchange_name, adapter = exchange_router.get_exchange(payload.symbol)

    idem_key = build_idempotency_key(payload)
    if idempotency_store.is_duplicate(idem_key):
        logger.info(
            "Duplicate event skipped",
            extra={"symbol": payload.symbol, "action": payload.action, "exchange": exchange_name},
        )
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "duplicate": True,
                "exchange": exchange_name,
                "request_id": request.state.request_id,
            },
        )

    qty_str = str(payload.qty)
    order_result: Dict[str, Any] | None = None

    if settings.dry_run:
        logger.info(
            "DRY_RUN: order not sent",
            extra={
                "symbol": payload.symbol,
                "action": payload.action,
                "exchange": exchange_name,
                "status": "dry_run",
            },
        )
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "dry_run": True,
                "exchange": exchange_name,
                "request_id": request.state.request_id,
            },
        )

    try:
        if payload.action == "BUY":
            order_result = adapter.create_market_buy(symbol=payload.symbol, qty=qty_str)
        elif payload.action == "CLOSE":
            order_result = adapter.create_market_sell(symbol=payload.symbol, qty=qty_str)
        else:
            raise HTTPException(status_code=400, detail="Unsupported action")
    except ExchangeError as exc:
        logger.error(
            "Order failed",
            extra={
                "symbol": payload.symbol,
                "action": payload.action,
                "exchange": exchange_name,
                "status": "error",
                "error_code": "exchange_error",
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Exchange order failed") from exc

    logger.info(
        "Order placed",
        extra={
            "symbol": payload.symbol,
            "action": payload.action,
            "exchange": exchange_name,
            "status": "sent",
        },
    )

    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "exchange": exchange_name,
            "result": order_result,
            "request_id": request.state.request_id,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
