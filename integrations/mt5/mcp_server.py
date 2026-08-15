"""MCP server that exposes cached MT5 bridge data as tools for Hermes Agent."""

from __future__ import annotations

import asyncio
import json
import os

from mcp.server.fastmcp import FastMCP

QUERY_HOST = os.environ.get("MT5_QUERY_HOST", "127.0.0.1")
QUERY_PORT = int(os.environ.get("MT5_QUERY_PORT", "18789"))

mcp = FastMCP("mt5-bridge")


async def _query(payload: dict) -> dict:
    reader, writer = await asyncio.open_connection(QUERY_HOST, QUERY_PORT)

    try:
        writer.write((json.dumps(payload) + "\n").encode("utf-8"))
        await writer.drain()

        line = await asyncio.wait_for(reader.readline(), timeout=5)

        if not line:
            return {"error": "no response from bridge query API"}

        return json.loads(line.decode("utf-8"))
    except (ConnectionRefusedError, asyncio.TimeoutError) as exc:
        return {"error": f"cannot reach MT5 bridge: {exc}"}
    finally:
        writer.close()

        try:
            await writer.wait_closed()
        except Exception:
            pass


@mcp.tool()
async def mt5_get_account() -> str:
    """Get the latest known MT5 account snapshot (balance, equity, margin, currency, broker, server)."""
    result = await _query({"type": "get_account"})
    return json.dumps(result, indent=2)


@mcp.tool()
async def mt5_get_positions() -> str:
    """Get the latest known list of open MT5 positions (symbol, type, volume, price, sl, tp, profit)."""
    result = await _query({"type": "get_positions"})
    return json.dumps(result, indent=2)


@mcp.tool()
async def mt5_get_orders() -> str:
    """Get the latest known list of pending MT5 orders (symbol, type, volume, price, sl, tp)."""
    result = await _query({"type": "get_orders"})
    return json.dumps(result, indent=2)


@mcp.tool()
async def mt5_status() -> str:
    """Get the connection status of all EA clients connected to the MT5 bridge (authenticated, last_seen, etc)."""
    result = await _query({"type": "status"})
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    asyncio.run(mcp.run_stdio_async())
