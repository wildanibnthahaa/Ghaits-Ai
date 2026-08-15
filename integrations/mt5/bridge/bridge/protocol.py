"""JSON-lines protocol helpers for Ghaits MT5 Bridge V1."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

PROTOCOL_VERSION = 1

def new_id(prefix: str = "req") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"

def make_message(message_type: str, request_id: str = "", **payload: Any) -> dict[str, Any]:
    message = {
        "v": PROTOCOL_VERSION,
        "type": message_type,
        "id": request_id,
        "ts": time.time(),
    }
    message.update(payload)
    return message

def encode(message: dict[str, Any]) -> bytes:
    return (json.dumps(message, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")

def decode(line: bytes | str) -> dict[str, Any]:
    if isinstance(line, bytes):
        line = line.decode("utf-8")

    value = json.loads(line)

    if not isinstance(value, dict):
        raise ValueError("protocol message must be a JSON object")

    return value
