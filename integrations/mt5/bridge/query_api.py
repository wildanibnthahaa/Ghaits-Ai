"""Local read-only query API for cached MT5 data (used by the MCP bridge)."""

from __future__ import annotations

import asyncio
import logging

from .protocol import decode, encode
from .registry import ClientRegistry

log = logging.getLogger("ghaits.mt5.bridge.query")


class QueryServer:
    def __init__(self, registry: ClientRegistry, pairing=None) -> None:
        self.registry = registry
        self.pairing = pairing
        self.server: asyncio.AbstractServer | None = None

    def _pick_client(self, account: str = ""):
        clients = self.registry.authenticated()

        if account:
            clients = [c for c in clients if c.account_login == account]

        return clients[0] if clients else None

    async def handle(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            while True:
                line = await reader.readline()

                if not line:
                    break

                line = line.strip()

                if not line:
                    continue

                try:
                    message = decode(line)
                except Exception as exc:
                    writer.write(encode({"type": "error", "message": str(exc)}))
                    await writer.drain()
                    continue

                query_type = str(message.get("type", ""))
                account = str(message.get("account", ""))

                if query_type == "status":
                    response = {
                        "type": "status_ok",
                        "clients": self.registry.summary(),
                    }
                elif query_type == "get_account":
                    client = self._pick_client(account)
                    response = {
                        "type": "account_ok" if client else "error",
                        "data": client.latest_account if client else None,
                        "message": None if client else "no authenticated EA connected",
                    }
                elif query_type == "get_positions":
                    client = self._pick_client(account)
                    response = {
                        "type": "positions_ok" if client else "error",
                        "data": client.latest_positions if client else None,
                        "message": None if client else "no authenticated EA connected",
                    }
                elif query_type == "get_orders":
                    client = self._pick_client(account)
                    response = {
                        "type": "orders_ok" if client else "error",
                        "data": client.latest_orders if client else None,
                        "message": None if client else "no authenticated EA connected",
                    }
                elif query_type == "pnl_card":
                    client = self._pick_client(account)

                    if not client or not client.latest_account:
                        response = {
                            "type": "error",
                            "message": "no authenticated EA connected or no account data yet",
                        }
                    else:
                        from .daily import update_and_get_anchors

                        acc = client.latest_account
                        balance = float(acc.get("balance", 0))
                        currency = acc.get("currency", "USD")
                        anchors = update_and_get_anchors(client.account_login, balance)

                        day_open = anchors["day_open_balance"]
                        all_time_open = anchors["all_time_open_balance"]

                        daily_pnl = balance - day_open
                        daily_pnl_pct = (daily_pnl / day_open * 100) if day_open else 0.0
                        total_pnl_pct = (
                            (balance - all_time_open) / all_time_open * 100
                        ) if all_time_open else 0.0

                        open_positions = len(client.latest_positions or [])

                        response = {
                            "type": "pnl_card_ok",
                            "data": {
                                "dailyPnl": daily_pnl,
                                "dailyPnlPct": daily_pnl_pct,
                                "totalPnlPct": total_pnl_pct,
                                "openPositions": open_positions,
                                "currency": currency,
                                "memberName": client.account_login,
                                "mode": client.mode or "Live",
                            },
                        }
                elif query_type == "new_pairing":
                    if self.pairing is None:
                        response = {"type": "error", "message": "pairing manager not available"}
                    else:
                        pairing = self.pairing.create()
                        response = {
                            "type": "pairing_ok",
                            "code": pairing.code,
                            "expires_at": pairing.expires_at,
                            "ttl_seconds": self.pairing.ttl_seconds,
                        }
                else:
                    response = {
                        "type": "error",
                        "message": f"unknown query type: {query_type}",
                    }

                writer.write(encode(response))
                await writer.drain()

        except (ConnectionError, BrokenPipeError):
            pass
        finally:
            writer.close()

            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def start(self, host: str, port: int) -> None:
        self.server = await asyncio.start_server(self.handle, host, port)

        log.info("Query API listening on %s:%s", host, port)

        async with self.server:
            await self.server.serve_forever()
