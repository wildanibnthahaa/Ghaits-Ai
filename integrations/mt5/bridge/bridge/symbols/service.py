"""Symbol discovery and canonical mapping service."""

from __future__ import annotations

from typing import Any

from .resolver import SymbolResolver


class SymbolService:
    def __init__(self) -> None:
        self._symbols: dict[str, list[str]] = {}
        self._mappings: dict[str, dict[str, str]] = {}

    def update_symbols(
        self,
        connection_id: str,
        symbols: list[str],
    ) -> dict[str, Any]:
        clean = sorted({
            str(symbol).strip()
            for symbol in symbols
            if str(symbol).strip()
        })

        self._symbols[connection_id] = clean

        return {
            "connection_id": connection_id,
            "count": len(clean),
            "symbols": clean,
        }

    def resolve(
        self,
        connection_id: str,
        canonicals: list[str],
    ) -> dict[str, Any]:
        available = self._symbols.get(connection_id, [])
        resolver = SymbolResolver(available)

        mappings: dict[str, str] = {}
        methods: dict[str, str] = {}
        unresolved: list[str] = []

        for canonical in canonicals:
            match = resolver.resolve(canonical)

            if match is None:
                unresolved.append(canonical)
                continue

            mappings[canonical] = match.broker_symbol
            methods[canonical] = match.method

        self._mappings[connection_id] = mappings

        return {
            "connection_id": connection_id,
            "mappings": mappings,
            "methods": methods,
            "unresolved": unresolved,
        }

    def get_mapping(self, connection_id: str) -> dict[str, str]:
        return dict(self._mappings.get(connection_id, {}))
