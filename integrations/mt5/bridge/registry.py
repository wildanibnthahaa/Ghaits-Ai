"""Connection and account registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

@dataclass
class Client:
    connection_id: str
    writer: Any
    bridge_id: str = ""
    client_id: str = ""
    account_login: str = ""
    broker: str = ""
    server: str = ""
    mode: str = ""
    timeframe: str = ""
    symbols: list[str] = field(default_factory=list)
    authenticated: bool = False
    paired: bool = False
    connected_at: float = field(default_factory=time)
    last_seen: float = field(default_factory=time)
    latest_account: dict[str, Any] | None = None
    latest_positions: list[Any] | None = None
    latest_orders: list[Any] | None = None

    def touch(self) -> None:
        self.last_seen = time()

    @property
    def identity(self) -> str:
        if self.bridge_id:
            return self.bridge_id
        if self.account_login:
            return f"account:{self.account_login}"
        return self.connection_id

class ClientRegistry:
    def __init__(self) -> None:
        self._clients: dict[str, Client] = {}

    def add(self, client: Client) -> None:
        self._clients[client.connection_id] = client

    def remove(self, connection_id: str) -> Client | None:
        return self._clients.pop(connection_id, None)

    def get(self, connection_id: str) -> Client | None:
        return self._clients.get(connection_id)

    def all(self) -> list[Client]:
        return list(self._clients.values())

    def authenticated(self) -> list[Client]:
        return [c for c in self._clients.values() if c.authenticated]

    def find_account(self, account_login: str, server: str = "") -> list[Client]:
        return [
            c for c in self._clients.values()
            if c.account_login == account_login
            and (not server or c.server == server)
        ]

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "connection_id": c.connection_id,
                "bridge_id": c.bridge_id,
                "client_id": c.client_id,
                "account_login": c.account_login,
                "broker": c.broker,
                "server": c.server,
                "mode": c.mode,
                "symbols": c.symbols,
                "authenticated": c.authenticated,
                "paired": c.paired,
                "last_seen": c.last_seen,
            }
            for c in self._clients.values()
        ]
