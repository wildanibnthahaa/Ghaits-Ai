"""Tracks day-open and all-time-open balance so PnL % can be computed
without a full trade-history database (we only keep the latest snapshot)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

STATE_FILE = Path.home() / ".ghaits_bridge_daily.json"


def _load() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(state: dict[str, Any]) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state))
    except OSError:
        pass


def update_and_get_anchors(account: str, balance: float) -> dict[str, float]:
    """Called each time a fresh account snapshot arrives. Records the
    day-open balance (resets when the date changes) and the all-time-open
    balance (set once, first time this account is ever seen). Returns both."""
    state = _load()
    entry = state.get(account, {})

    today = date.today().isoformat()

    if entry.get("day") != today:
        entry["day"] = today
        entry["day_open_balance"] = balance

    if "all_time_open_balance" not in entry:
        entry["all_time_open_balance"] = balance

    state[account] = entry
    _save(state)

    return {
        "day_open_balance": entry["day_open_balance"],
        "all_time_open_balance": entry["all_time_open_balance"],
    }
