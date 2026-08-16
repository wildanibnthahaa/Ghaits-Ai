"""Individual EA TCP connection handling."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from .auth import apply_identity, validate_auth
from .protocol import decode, encode, make_message
from .pairing import PairingManager
from .registry import Client, ClientRegistry
from .symbols.service import SymbolService
from .execution import ExecutionService
from .daily import update_and_get_anchors

log = logging.getLogger("ghaits.mt5.bridge")


class Connection:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        registry: ClientRegistry,
        mode: str = "paper",
        pairing: PairingManager | None = None,
        symbol_service: SymbolService | None = None,
        execution: ExecutionService | None = None,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.registry = registry
        self.mode = mode
        self.pairing = pairing or PairingManager()
        self.symbol_service = symbol_service or SymbolService()
        self.execution = execution or ExecutionService(mode=mode)

        # Requests sent from the bridge to the EA that are waiting
        # for an execution response.
        self._pending_requests: dict[str, asyncio.Future[dict[str, Any]]] = {}

        self.client = Client(
            connection_id=uuid.uuid4().hex,
            writer=writer,
        )

        self.registry.add(self.client)

    async def send(self, message: dict[str, Any]) -> None:
        self.writer.write(encode(message))
        await self.writer.drain()

    async def reply(
        self,
        message_type: str,
        request_id: str,
        **payload: Any,
    ) -> None:
        await self.send(
            make_message(
                message_type,
                request_id,
                **payload,
            )
        )

    async def send_to_ea(
        self,
        message: dict[str, Any],
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        """Send a command to the connected EA and wait for its response."""

        request_id = str(message.get("id", "")).strip()

        if not request_id:
            raise ValueError("EA command requires a request id")

        if not self.client.authenticated:
            raise RuntimeError("EA is not authenticated")

        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()

        self._pending_requests[request_id] = future

        try:
            await self.send(message)

            return await asyncio.wait_for(
                future,
                timeout=timeout,
            )

        except asyncio.TimeoutError as exc:
            raise RuntimeError(
                f"EA execution timeout for request {request_id}"
            ) from exc

        finally:
            self._pending_requests.pop(request_id, None)

    def resolve_pending_response(
        self,
        message: dict[str, Any],
    ) -> bool:
        request_id = str(message.get("id", "")).strip()

        if not request_id:
            return False

        future = self._pending_requests.get(request_id)

        if future is None or future.done():
            return False

        future.set_result(message)
        return True

    async def handle(
        self,
        message: dict[str, Any],
    ) -> None:
        self.client.touch()

        message_type = str(message.get("type", ""))
        request_id = str(message.get("id", ""))

        if message_type == "pairing_create":
            pairing = self.pairing.create()

            await self.reply(
                "pairing_created",
                request_id,
                code=pairing.code,
                expires_at=pairing.expires_at,
                ttl_seconds=self.pairing.ttl_seconds,
            )
            return

        if message_type == "auth":
            await self.handle_auth(message, request_id)
            return

        if not self.client.authenticated:
            await self.reply(
                "error",
                request_id,
                code="not_authenticated",
                message="EA must authenticate first",
            )
            return

        if message_type == "ping":
            await self.reply("pong", request_id)
            return

        if message_type == "place_order":
            symbol = str(message.get("symbol", "")).strip()
            side = str(message.get("side", "")).strip()
            volume = float(message.get("volume", 0))

            if not symbol:
                await self.reply(
                    "error",
                    request_id,
                    code="symbol_required",
                    message="symbol is required",
                )
                return

            # Resolve canonical Ghaits symbol to the broker's
            # actual MT5 symbol before execution.
            mapping = self.symbol_service.resolve(
                self.client.connection_id,
                [symbol],
            )

            if mapping["unresolved"]:
                await self.reply(
                    "error",
                    request_id,
                    code="symbol_not_found",
                    message=f"symbol '{symbol}' could not be resolved",
                    unresolved=mapping["unresolved"],
                )
                return

            broker_symbol = mapping["mappings"][symbol]
            resolution_method = mapping["methods"][symbol]

            order_type = str(
                message.get("order_type", "market")
            ).strip().lower()

            price = message.get("price")
            sl = message.get("sl")
            tp = message.get("tp")
            comment = str(
                message.get("comment", "ghaits")
            )

            if self.mode == "live":
                if order_type != "market":
                    await self.reply(
                        "error",
                        request_id,
                        code="unsupported_order_type",
                        message="live EA execution currently supports market orders only",
                    )
                    return

                ea_command = make_message(
                    "place_order",
                    request_id,
                    symbol=broker_symbol,
                    side=side,
                    volume=volume,
                    order_type=order_type,
                    price=price,
                    sl=sl,
                    tp=tp,
                    comment=comment,
                )

                try:
                    result = await self.send_to_ea(
                        ea_command,
                        timeout=15.0,
                    )
                except (RuntimeError, ValueError) as exc:
                    await self.reply(
                        "error",
                        request_id,
                        code="ea_execution_failed",
                        message=str(exc),
                    )
                    return

                result["canonical_symbol"] = symbol
                result["broker_symbol"] = broker_symbol
                result["resolution_method"] = resolution_method

                await self.send(result)
                return

            try:
                result = self.execution.place_order(
                    connection_id=self.client.connection_id,
                    symbol=broker_symbol,
                    side=side,
                    volume=volume,
                    order_type=order_type,
                    price=price,
                    sl=sl,
                    tp=tp,
                    comment=comment,
                )
            except (TypeError, ValueError, RuntimeError) as exc:
                await self.reply(
                    "error",
                    request_id,
                    code="order_rejected",
                    message=str(exc),
                )
                return

            result["canonical_symbol"] = symbol
            result["broker_symbol"] = broker_symbol
            result["resolution_method"] = resolution_method

            await self.reply(
                "order_ok",
                request_id,
                **result,
            )
            return

        if message_type == "orders":
            orders = self.execution.list_orders(
                self.client.connection_id
            )

            await self.reply(
                "orders_ok",
                request_id,
                orders=orders,
                count=len(orders),
            )
            return

        if message_type == "symbols":
            symbols = message.get("symbols", [])

            if not isinstance(symbols, list):
                await self.reply(
                    "error",
                    request_id,
                    code="symbols_must_be_array",
                    message="symbols must be an array",
                )
                return

            result = self.symbol_service.update_symbols(
                self.client.connection_id,
                symbols,
            )

            await self.reply(
                "symbols_ok",
                request_id,
                **result,
            )
            return

        if message_type == "resolve_symbols":
            canonicals = message.get("symbols", [])

            if not isinstance(canonicals, list):
                await self.reply(
                    "error",
                    request_id,
                    code="symbols_must_be_array",
                    message="symbols must be an array",
                )
                return

            result = self.symbol_service.resolve(
                self.client.connection_id,
                [
                    str(symbol).strip()
                    for symbol in canonicals
                    if str(symbol).strip()
                ],
            )

            await self.reply(
                "symbols_resolved",
                request_id,
                **result,
            )
            return

        if message_type in {
            "account",
            "account_ok",
            "positions",
            "positions_ok",
            "orders",
            "orders_ok",
            "deals",
            "tick",
        }:
            log.info(
                "DATA %s account=%s payload=%s",
                message_type,
                self.client.account_login,
                message,
            )

            if message_type in {"account", "account_ok"}:
                self.client.latest_account = message

                try:
                    balance = float(message.get("balance", 0))
                    update_and_get_anchors(self.client.account_login, balance)
                except (TypeError, ValueError):
                    pass
            elif message_type in {"positions", "positions_ok"}:
                self.client.latest_positions = message.get("positions")
            elif message_type in {"orders", "orders_ok"}:
                self.client.latest_orders = message.get("orders")

            await self.reply(
                "ack",
                request_id,
                accepted=True,
            )
            return

        await self.reply(
            "error",
            request_id,
            code="unknown_message_type",
            message=message_type,
        )

    async def handle_auth(
        self,
        message: dict[str, Any],
        request_id: str,
    ) -> None:
        valid, error = validate_auth(message)

        if not valid:
            await self.reply(
                "error",
                request_id,
                code="invalid_auth",
                message=error,
            )
            return

        apply_identity(self.client, message)

        pair_token = str(message.get("pair_token", "")).strip()

        if not pair_token:
            await self.reply(
                "error",
                request_id,
                code="pairing_required",
                message="valid pairing code is required",
            )
            return

        pairing_valid, pairing_error = self.pairing.validate(
            code=pair_token,
            account=self.client.account_login,
            broker=self.client.broker,
            server=self.client.server,
        )

        if not pairing_valid:
            await self.reply(
                "error",
                request_id,
                code="pairing_failed",
                message=pairing_error,
            )
            return

        if not self.pairing.consume(pair_token):
            await self.reply(
                "error",
                request_id,
                code="pairing_failed",
                message="pairing_already_used_or_expired",
            )
            return

        self.client.authenticated = True
        self.client.paired = True
        self.client.mode = self.mode

        await self.reply(
            "auth_ok",
            request_id,
            connection_id=self.client.connection_id,
            bridge_id=self.client.bridge_id,
            account=self.client.account_login,
            broker=self.client.broker,
            server=self.client.server,
            symbols=self.client.symbols,
            mode=self.mode,
        )

        log.info(
            "authenticated account=%s broker=%s server=%s symbols=%s",
            self.client.account_login,
            self.client.broker,
            self.client.server,
            self.client.symbols,
        )

    async def run(self) -> None:
        peer = self.writer.get_extra_info("peername")

        log.info(
            "EA connected peer=%s connection=%s",
            peer,
            self.client.connection_id,
        )

        try:
            while True:
                line = await self.reader.readline()

                if not line:
                    break

                # Ignore empty / whitespace / null-only packets.
                clean_line = line.replace(b"\\x00", b"").strip()

                if not clean_line:
                    continue

                message = None

                try:
                    message = decode(clean_line)

                    # First, resolve responses belonging to commands
                    # previously sent from the bridge to the EA.
                    if self.resolve_pending_response(message):
                        continue

                    await self.handle(message)

                except Exception as exc:
                    log.exception("protocol error")

                    request_id = ""

                    if isinstance(message, dict):
                        request_id = str(
                            message.get("id", "")
                        )

                    # Never let a malformed packet kill the EA session.
                    try:
                        await self.reply(
                            "error",
                            request_id,
                            code="protocol_error",
                            message=str(exc),
                        )
                    except (ConnectionError, BrokenPipeError):
                        break

        finally:
            removed = self.registry.remove(
                self.client.connection_id
            )

            if removed:
                log.info(
                    "EA disconnected account=%s connection=%s",
                    removed.account_login,
                    removed.connection_id,
                )

            self.writer.close()

            try:
                await self.writer.wait_closed()
            except Exception:
                pass
