# TradingView Webhook Order Backend (Binance + Bybit)

FastAPI service that receives TradingView alerts and routes spot market orders to Binance or Bybit with optional dry-run mode, HMAC verification, and in-memory idempotency.

## Features
- Passphrase check (`payload.passphrase` vs `TV_PASSPHRASE`) and optional `X-Signature` HMAC verification.
- Exchange selection via `EXCHANGE_DEFAULT` and `EXCHANGE_SYMBOL_MAP` (per-symbol overrides).
- Spot-only MARKET `BUY` and `CLOSE` (sell) actions; `qty` is required for CLOSE.
- In-memory TTL idempotency to drop duplicates within the window.
- DRY_RUN mode logs intended orders without hitting exchanges.
- Structured JSON logging with `request_id`, symbol, action, exchange, and outcome.

## Setup
1) Python 3.10+ recommended.  
2) `python -m venv .venv && source .venv/bin/activate`  
3) `pip install -r requirements.txt`  
4) Copy `.env.example` to `.env` and fill in secrets (`TV_PASSPHRASE`, API keys). Leave `TV_WEBHOOK_HMAC_SECRET` empty to disable HMAC for local testing.

## Run locally
```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Health: `curl http://localhost:8000/health`  
Version: `curl http://localhost:8000/version`

## Test webhook (curl)
```
curl -X POST http://localhost:8000/webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "passphrase": "change-me",
    "symbol": "BTCUSDT",
    "action": "BUY",
    "qty": "0.001",
    "type": "MARKET",
    "ts": 1730000000000,
    "event_id": "demo-1",
    "strategy": "AI - Squeeze Momentum Deluxe"
  }'
```
If `TV_WEBHOOK_HMAC_SECRET` is set, include `X-Signature` as `hex(hmac_sha256(secret, raw_body))`.

## DRY_RUN
Set `DRY_RUN=true` to log intended orders without placing them. Set to `false` for live trading (requires API keys).

## Exchange credentials
- Binance: `BINANCE_API_KEY`, `BINANCE_API_SECRET`
- Bybit: `BYBIT_API_KEY`, `BYBIT_API_SECRET`
Keys are read from the environment and never hardcoded; keep `.env` out of version control.

## Security notes
- Use strong `TV_PASSPHRASE` and HTTPS/secure ingress for the webhook.
- Enable HMAC with `TV_WEBHOOK_HMAC_SECRET` for authenticity, and rotate secrets regularly.
- This MVP holds no database; idempotency is in-memory TTL only and will reset on restart.
