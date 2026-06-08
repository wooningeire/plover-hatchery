from typing import Any, Protocol

from plover_hatchery.lib.sopheme import Keysymbol


KeysymbolDescription = tuple[str, str, int, bool]


class ParsedKeysymbol(Protocol):
    value: str
    stress: int
    optional: bool
    kind: Any


def _describe(keysymbols: tuple[ParsedKeysymbol, ...]) -> tuple[KeysymbolDescription, ...]:
    return tuple(
        (
            keysymbol.value,
            keysymbol.kind.kind_name,
            keysymbol.stress,
            keysymbol.optional,
        )
        for keysymbol in keysymbols
    )


def test__parse_seq__ignores_markup_and_applies_pending_stress() -> None:
    assert _describe(Keysymbol.parse_seq(" { ~ [A1] . k * e } ")) == (
        ("a", "abstract", 2, True),
        ("k", "abstract", 0, False),
        ("e", "abstract", 1, False),
    )


def test__normalize_stress__renumbers_relative_to_primary_stress() -> None:
    keysymbols = Keysymbol.parse_seq(" ~ a - o s ")

    normalized, max_stress = Keysymbol.normalize_stress(keysymbols)

    assert max_stress == 2
    assert _describe(normalized) == (
        ("a", "abstract", 1, False),
        ("o", "abstract", 2, False),
        ("s", "abstract", 0, False),
    )
