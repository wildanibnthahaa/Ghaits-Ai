"""Canonical-to-broker MT5 symbol resolver."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolMatch:
    canonical: str
    broker_symbol: str
    method: str


class SymbolResolver:
    """
    Resolve canonical trading symbols against symbols exposed by MT5.

    Resolution order:
    1. Exact match.
    2. Case-insensitive exact match.
    3. Common suffix/prefix variants.
    """

    def __init__(self, available_symbols: list[str]) -> None:
        self.available_symbols = [
            symbol.strip()
            for symbol in available_symbols
            if symbol.strip()
        ]

    def resolve(self, canonical: str) -> SymbolMatch | None:
        canonical = canonical.strip()

        if not canonical:
            return None

        # 1. Exact match.
        if canonical in self.available_symbols:
            return SymbolMatch(
                canonical=canonical,
                broker_symbol=canonical,
                method="exact",
            )

        # 2. Case-insensitive exact match.
        canonical_upper = canonical.upper()

        for symbol in self.available_symbols:
            if symbol.upper() == canonical_upper:
                return SymbolMatch(
                    canonical=canonical,
                    broker_symbol=symbol,
                    method="case_insensitive",
                )

        # 3. Common broker suffix/prefix variants.
        variants = (
            "m",
            "M",
            "c",
            "C",
            "x",
            "X",
            ".m",
            ".M",
            "_m",
            "_M",
            "-m",
            "-M",
        )

        for suffix in variants:
            candidate = canonical + suffix

            if candidate in self.available_symbols:
                return SymbolMatch(
                    canonical=canonical,
                    broker_symbol=candidate,
                    method="suffix",
                )

        for symbol in self.available_symbols:
            symbol_upper = symbol.upper()

            if (
                symbol_upper.startswith(canonical_upper)
                and len(symbol) > len(canonical)
            ):
                return SymbolMatch(
                    canonical=canonical,
                    broker_symbol=symbol,
                    method="prefix_match",
                )

        return None

    def resolve_many(
        self,
        canonicals: list[str],
    ) -> dict[str, SymbolMatch | None]:
        return {
            canonical: self.resolve(canonical)
            for canonical in canonicals
        }
