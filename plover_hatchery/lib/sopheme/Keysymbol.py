from collections.abc import Iterable, Generator
import re

from plover_hatchery_lib_rs import Keysymbol



_KEYSYMBOL_REMOVE_SUB = re.compile(r"[\[\]\d]")
_NONPHONETIC_KEYSYMBOLS = tuple("*~-.<>{}#=$")
_STRESS_KEYSYMBOLS = {
    "*": 1,
    "~": 2,
    "-": 3,
}


def stress_marker(stress: int):
    if stress <= 0:
        return ""
    return f"!{stress}"



def parse_seq(transcription: str):
    phonetic_keysymbols: list[Keysymbol] = []
    next_stress = 0
    for keysymbol in transcription.split(" "):
        if len(keysymbol) == 0: continue

        if keysymbol in _STRESS_KEYSYMBOLS:
            next_stress = _STRESS_KEYSYMBOLS[keysymbol]

        if any(ch in keysymbol for ch in _NONPHONETIC_KEYSYMBOLS): continue

        optional = keysymbol.startswith("[") and keysymbol.endswith("]")
        phonetic_keysymbols.append(Keysymbol(_KEYSYMBOL_REMOVE_SUB.sub("", keysymbol).lower(), next_stress, optional))

        next_stress = 0

    return tuple(phonetic_keysymbols)

def max_stress_value(stress_values: Iterable[int]):
    max_stress = 0
    for stress in stress_values:
        if stress == 0: continue

        if max_stress == 0 or stress < max_stress:
            max_stress = stress
    
    return max_stress

def adjust_stress(stress_values: Iterable[int], max_stress: int) -> Generator[int, None, None]:
    for stress in stress_values:
        if stress == 0:
            yield 0
        else:
            yield stress - max_stress + 1

def adjust_keysymbol_stress(keysymbols: "tuple[Keysymbol, ...]", max_stress: int) -> "Generator[Keysymbol, None, None]":
    if max_stress == 0:
        yield from keysymbols
        return

    for keysymbol, stress in zip(keysymbols, adjust_stress((keysymbol.stress for keysymbol in keysymbols), max_stress)):
        if stress == 0:
            yield keysymbol
        else:
            yield Keysymbol(keysymbol.symbol, stress, keysymbol.optional)


def normalize_stress(keysymbols: "tuple[Keysymbol, ...]") -> "tuple[tuple[Keysymbol, ...], int]":
    max_stress = max_stress_value(keysymbol.stress for keysymbol in keysymbols)
    new_keysymbols = tuple(adjust_keysymbol_stress(keysymbols, max_stress))
    return (new_keysymbols, max_stress)