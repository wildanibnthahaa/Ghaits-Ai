"""MCP server that exposes cached MT5 bridge data as tools for Hermes Agent."""

from __future__ import annotations

import asyncio
import json
import os

from mcp.server.fastmcp import FastMCP, Image

QUERY_HOST = os.environ.get("MT5_QUERY_HOST", "127.0.0.1")
QUERY_PORT = int(os.environ.get("MT5_QUERY_PORT", "18789"))
DEFAULT_MEMBER_NAME = os.environ.get("MT5_MEMBER_NAME", "")

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


@mcp.tool()
async def mt5_generate_pnl_card(member_name: str = "") -> Image:
    """Generate today's PnL card as a branded PNG image (balance, daily PnL, open positions).
    Use this when the member asks for their PnL, daily performance, or trading report/card.

    Args:
        member_name: The Telegram username or display name of the person you are
            currently chatting with (without the @ symbol), so it can be shown on
            the card. Always pass this from your conversation context if you know it.
    """
    import sys
    from pathlib import Path as _Path

    sys.path.insert(0, str(_Path(__file__).resolve().parent))
    from report.render import build_pnl_card_svg, rasterize

    result = await _query({"type": "pnl_card"})

    if result.get("type") != "pnl_card_ok":
        raise RuntimeError(result.get("message", "gagal mengambil data PnL"))

    data = dict(result["data"])
    resolved_name = DEFAULT_MEMBER_NAME.strip() or member_name.strip()
    if resolved_name:
        data["memberName"] = resolved_name

    svg = build_pnl_card_svg(data)
    png_bytes = rasterize(svg)

    return Image(data=png_bytes, format="png")


@mcp.tool()
async def mt5_new_pairing() -> str:
    """Generate a fresh MT5 EA pairing code. Use this whenever the member asks to connect, reconnect, or pair their MetaTrader EA. Give the returned code directly to the member in chat, and remind them it expires after a limited time and must be entered into InpPairingCode in their EA before re-attaching it."""
    result = await _query({"type": "new_pairing"})
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    asyncio.run(mcp.run_stdio_async())
