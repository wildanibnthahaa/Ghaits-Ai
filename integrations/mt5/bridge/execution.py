"""Dry-run execution service for Ghaits MT5 Bridge V1."""

from __future__ import annotations

from typing import Any


class ExecutionService:
    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._orders: dict[str, dict[str, Any]] = {}

    def place_order(
        self,
        connection_id: str,
        symbol: str,
        side: str,
        volume: float,
        order_type: str = "market",
        price: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        comment: str = "ghaits",
    ) -> dict[str, Any]:
        side = side.lower().strip()
        order_type = order_type.lower().strip()

        if side not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")

        if volume <= 0:
            raise ValueError("volume must be greater than zero")

        if order_type not in {"market", "limit", "stop"}:
            raise ValueError("unsupported order_type")

        order_id = f"dryrun-{len(self._orders) + 1:06d}"

        result = {
            "order_id": order_id,
            "connection_id": connection_id,
            "symbol": symbol,
            "side": side,
            "volume": volume,
            "order_type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "comment": comment,
            "status": "accepted",
            "dry_run": self.dry_run,
        }

        self._orders[order_id] = result
        return result

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        return self._orders.get(order_id)

    def list_orders(self, connection_id: str) -> list[dict[str, Any]]:
        return [
            order
            for order in self._orders.values()
            if order["connection_id"] == connection_id
        ]
