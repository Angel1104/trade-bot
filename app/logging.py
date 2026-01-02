from __future__ import annotations

import contextvars
import datetime
import json
import logging
import sys
from typing import Any, Dict

request_id_ctx_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_ctx_var.get()
        if request_id:
            payload["request_id"] = request_id

        for attr in ("symbol", "action", "exchange", "status", "error_code"):
            if hasattr(record, attr):
                payload[attr] = getattr(record, attr)

        # Capture structured extras if present
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # quiet noisy libraries
    logging.getLogger("uvicorn.access").propagate = False
