"""Runtime state for the MT5 bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BridgeState:
    dry_run: bool = True
    ready: bool = False
    clients: dict[str, dict[str, Any]] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "ready": self.ready,
            "clients": self.clients,
        }
