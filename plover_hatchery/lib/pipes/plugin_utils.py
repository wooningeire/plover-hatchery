from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import TypeVar

from plover.steno import Stroke

from plover_hatchery_lib_rs import Soph


T = TypeVar("T")


def join_sophs_to_chords_dicts(dicts: Iterable[dict[str, str]], collect: Callable[[Iterable[Stroke]], T]=tuple[Stroke, ...]):
    aggregated_dict: dict[tuple[Soph, ...], list[Stroke]] = defaultdict(list)

    for dict_ in dicts:
        for soph_values, chord_stenos in dict_.items():
            sophs = Soph.parse_seq(soph_values)
            aggregated_dict[sophs].extend(Stroke(steno) for steno in chord_stenos.split())

    return {
        sophs: collect(chords)
        for sophs, chords in aggregated_dict.items()
    }


def iife(fn: Callable[[], T]) -> T:
    return fn()