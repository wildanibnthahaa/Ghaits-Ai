"""Minimal SVG->PNG rasterizer for the PnL card (font registration + cairosvg)."""

from __future__ import annotations

import ctypes
import ctypes.util
from pathlib import Path

_FONTS_REGISTERED = False


def _register_bundled_fonts() -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    _FONTS_REGISTERED = True

    lib_path = ctypes.util.find_library("fontconfig")
    if not lib_path:
        return
    try:
        fc = ctypes.CDLL(lib_path)
        fc.FcConfigGetCurrent.restype = ctypes.c_void_p
        fc.FcConfigGetCurrent.argtypes = []
        fc.FcConfigAppFontAddFile.restype = ctypes.c_int
        fc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        cfg = fc.FcConfigGetCurrent()
        fonts_dir = Path(__file__).resolve().parent / "fonts"
        for font_file in fonts_dir.glob("*.ttf"):
            fc.FcConfigAppFontAddFile(cfg, str(font_file).encode("utf-8"))
    except OSError:
        pass


def rasterize(svg: str) -> bytes:
    import cairosvg

    _register_bundled_fonts()
    return cairosvg.svg2png(bytestring=svg.encode("utf-8"))


def escape_xml(value) -> str:
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_money(value, currency: str = "USD", *, signed: bool = False) -> str:
    number = float(value or 0)
    sign = "+" if (signed and number >= 0) else ("-" if signed and number < 0 else "")
    abs_num = abs(number)
    grouped = f"{abs_num:,.2f}"
    return f"{sign}${grouped}"


def build_pnl_card_svg(data: dict) -> str:
    from .pnl_card_template import PNL_CARD_TEMPLATE

    daily_pnl = float(data.get("dailyPnl") or 0)
    daily_pnl_pct = float(data.get("dailyPnlPct") or 0)
    total_pnl_pct = float(data.get("totalPnlPct") or 0)
    open_positions = int(data.get("openPositions") or 0)
    currency = data.get("currency", "USD")
    member_name = str(data.get("memberName") or "Ghaits Trader").strip()
    mode = str(data.get("mode") or "Live")

    pnl_color = "#05DF72" if daily_pnl >= 0 else "#EE4623"

    return PNL_CARD_TEMPLATE.format(
        pnl_usd=escape_xml(format_money(daily_pnl, currency, signed=True)),
        pnl_perc=escape_xml(f"{daily_pnl_pct:+.2f}%"),
        pnl_color=pnl_color,
        timeframe="Daily",
        yoy_chg=escape_xml(f"{total_pnl_pct:+.1f}%"),
        yoy_pos=str(open_positions) + " open",
        username=escape_xml(member_name),
        mode_label=escape_xml(mode),
    )
