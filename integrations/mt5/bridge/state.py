"""Runtime state for the MT5 bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_MODES = {"paper", "live"}


@dataclass
class BridgeState:
    mode: str = "paper"
    ready: bool = False
    clients: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.mode = str(self.mode).strip().lower()

        if self.mode not in VALID_MODES:
            raise ValueError(f"unsupported bridge mode: {self.mode}")

    def snapshot(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ready": self.ready,
            "clients": self.clients,
        }
