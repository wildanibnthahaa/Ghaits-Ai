"""Temporary pairing-code lifecycle for Ghaits MT5 Bridge V1."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass


@dataclass
class PairingCode:
    code: str
    expires_at: float
    used: bool = False
    account: str = ""
    broker: str = ""
    server: str = ""


class PairingManager:
    def __init__(self, ttl_seconds: int = 600) -> None:
        self.ttl_seconds = ttl_seconds
        self._codes: dict[str, PairingCode] = {}

    def create(
        self,
        account: str = "",
        broker: str = "",
        server: str = "",
    ) -> PairingCode:
        raw = secrets.token_hex(6).upper()
        code = f"GHAITS-{raw[:4]}-{raw[4:8]}-{raw[8:12]}"

        item = PairingCode(
            code=code,
            expires_at=time.time() + self.ttl_seconds,
            account=account,
            broker=broker,
            server=server,
        )

        self._codes[code] = item
        return item

    def validate(
        self,
        code: str,
        account: str,
        broker: str,
        server: str,
    ) -> tuple[bool, str]:
        self.cleanup()

        item = self._codes.get(code)

        if item is None:
            return False, "invalid_or_expired_pairing"

        if item.used:
            return False, "pairing_already_used"

        if item.account and item.account != account:
            return False, "pairing_account_mismatch"

        if item.broker and item.broker != broker:
            return False, "pairing_broker_mismatch"

        if item.server and item.server != server:
            return False, "pairing_server_mismatch"

        return True, ""

    def consume(self, code: str) -> bool:
        item = self._codes.get(code)

        if item is None:
            return False

        if time.time() >= item.expires_at:
            self._codes.pop(code, None)
            return False

        # Pairing is intentionally reusable while it is valid.
        # The EA needs the same credential after a TCP reconnect.
        item.used = False

        return True

    def cleanup(self) -> None:
        now = time.time()

        expired = [
            code
            for code, item in self._codes.items()
            if item.expires_at <= now
        ]

        for code in expired:
            self._codes.pop(code, None)
