from typing import Protocol

from plover_hatchery.lib.sopheme import Keysymbol


KeysymbolDescription = tuple[str, str, int, bool]


class ParsedKeysymbol(Protocol):
    symbol: str
    base_symbol: str
    stress: int
    optional: bool


def _describe(keysymbols: tuple[ParsedKeysymbol, ...]) -> tuple[KeysymbolDescription, ...]:
    return tuple(
        (keysymbol.symbol, keysymbol.base_symbol, keysymbol.stress, keysymbol.optional)
        for keysymbol in keysymbols
    )


def test__parse_seq__ignores_markup_and_applies_pending_stress() -> None:
    assert _describe(Keysymbol.parse_seq(" { ~ [A1] . k * e } ")) == (
        ("a", "a", 2, True),
        ("k", "k", 0, False),
        ("e", "e", 1, False),
    )


def test__normalize_stress__renumbers_relative_to_primary_stress() -> None:
    keysymbols = Keysymbol.parse_seq(" ~ a - o s ")

    normalized, max_stress = Keysymbol.normalize_stress(keysymbols)

    assert max_stress == 2
    assert _describe(normalized) == (
        ("a", "a", 1, False),
        ("o", "o", 2, False),
        ("s", "s", 0, False),
    )
