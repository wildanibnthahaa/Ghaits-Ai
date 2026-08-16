"""Ghaits MT5 Bridge Server V1."""

from __future__ import annotations

import argparse
import asyncio
import logging

from .connection import Connection
from .pairing import PairingManager
from .query_api import QueryServer
from .registry import ClientRegistry
from .state import BridgeState
from .symbols.service import SymbolService
from .execution import ExecutionService


log = logging.getLogger("ghaits.mt5.bridge")


class BridgeServer:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 18788,
        query_port: int = 18789,
        mode: str = "paper",
    ) -> None:
        self.host = host
        self.port = port
        self.query_port = query_port

        self.registry = ClientRegistry()
        self.pairing = PairingManager()
        self.pairing_code = self.pairing.create()
        self.state = BridgeState(mode=mode)
        self.symbol_service = SymbolService()
        self.execution = ExecutionService(mode=mode)
        self.query_server = QueryServer(self.registry, self.pairing)

        self.server: asyncio.AbstractServer | None = None

    async def client_connected(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        connection = Connection(
            reader=reader,
            writer=writer,
            registry=self.registry,
            mode=self.state.mode,
            pairing=self.pairing,
            symbol_service=self.symbol_service,
            execution=self.execution,
        )

        await connection.run()

    async def start(self) -> None:
        self.server = await asyncio.start_server(
            self.client_connected,
            self.host,
            self.port,
        )

        self.state.ready = True

        sockets = self.server.sockets or []

        addresses = ", ".join(
            str(sock.getsockname())
            for sock in sockets
        )

        log.info(
            "Ghaits MT5 Bridge V1 listening on %s",
            addresses,
        )
        log.info(
            "Ghaits MT5 Bridge pairing code: %s (expires in %ss)",
            self.pairing_code.code,
            self.pairing.ttl_seconds,
        )

        asyncio.create_task(
            self.query_server.start(self.host, self.query_port)
        )

        async with self.server:
            await self.server.serve_forever()

    async def stop(self) -> None:
        self.state.ready = False

        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ghaits MT5 Bridge V1",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=18788,
    )

    parser.add_argument(
        "--query-port",
        type=int,
        default=18789,
    )

    parser.add_argument(
        "--mode",
        choices=("paper", "live"),
        default="paper",
        help="Execution mode: paper or live.",
    )

    parser.add_argument(
        "--pairing",
        action="store_true",
        help="Generate a temporary MT5 pairing code and exit.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    server = BridgeServer(
        host=args.host,
        port=args.port,
        query_port=args.query_port,
        mode=args.mode,
    )

    if args.pairing:
        pairing = server.pairing.create()
        print(pairing.code)
        return

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        log.info("Bridge stopped")


if __name__ == "__main__":
    main()
