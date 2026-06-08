from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import TypeVar

from plover.steno import Stroke

from plover_hatchery_lib_rs import TheorySymbol


T = TypeVar("T")


def join_theory_symbols_to_chords_dicts(dicts: Iterable[dict[str, str]], collect: Callable[[Iterable[Stroke]], T]=tuple[Stroke, ...]):
    aggregated_dict: dict[tuple[TheorySymbol, ...], list[Stroke]] = defaultdict(list)

    for dict_ in dicts:
        for theory_symbol_values, chord_stenos in dict_.items():
            theory_symbols = TheorySymbol.parse_seq(theory_symbol_values)
            aggregated_dict[theory_symbols].extend(Stroke(steno) for steno in chord_stenos.split())

    return {
        theory_symbols: collect(chords)
        for theory_symbols, chords in aggregated_dict.items()
    }


def iife(fn: Callable[[], T]) -> T:
    return fn()