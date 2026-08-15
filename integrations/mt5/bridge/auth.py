"""EA authentication and identity validation."""

from __future__ import annotations

from typing import Any

from .registry import Client


REQUIRED_IDENTITY_FIELDS = (
    "account",
    "broker",
    "server",
)


def validate_auth(message: dict[str, Any]) -> tuple[bool, str]:
    for field in REQUIRED_IDENTITY_FIELDS:
        value = str(message.get(field, "")).strip()

        if not value:
            return False, f"missing_identity:{field}"

    symbols = message.get("symbols", [])

    if not isinstance(symbols, list):
        return False, "symbols_must_be_array"

    return True, ""


def apply_identity(
    client: Client,
    message: dict[str, Any],
) -> None:
    client.bridge_id = str(message.get("bridge_id", "")).strip()
    client.client_id = str(message.get("client_id", "")).strip()
    client.account_login = str(message.get("account", "")).strip()
    client.broker = str(message.get("broker", "")).strip()
    client.server = str(message.get("server", "")).strip()
    client.mode = str(message.get("mode", "")).strip()
    client.timeframe = str(message.get("timeframe", "")).strip()

    client.symbols = [
        str(symbol).strip()
        for symbol in message.get("symbols", [])
        if str(symbol).strip()
    ]
