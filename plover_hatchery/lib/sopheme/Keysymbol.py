from collections.abc import Iterable
import dataclasses
from dataclasses import dataclass
import re
from typing import Any, Generator


_vowel_symbols = {
    "e",
    "ao",
    "a",
    "ah",
    "oa",
    "aa",
    "ar",
    "eh",
    "ou",
    "ouw",
    "oou",
    "o",
    "au",
    "oo",
    "or",
    "our",
    "ii",
    "iy",
    "i",
    "@r",
    "@",
    "uh",
    "u",
    "uu",
    "iu",
    "ei",
    "ee",
    "ai",
    "ae",
    "aer",
    "aai",
    "oi",
    "oir",
    "ow",
    "owr",
    "oow",
    "ir",
    "@@r",
    "er",
    "eir",
    "ur",
    "i@",
}

_KEYSYMBOL_SUB = re.compile(r"[\[\]\d]")
_KEYSYMBOL_OPTIONAL_SUB= re.compile(r"[\[\]]")
_NONPHONETIC_KEYSYMBOLS = tuple("*~-.<>{}#=$")
_STRESS_KEYSYMBOLS = {
    "*": 1,
    "~": 2,
    "-": 3,
}


@dataclass(frozen=True)
class Keysymbol:
    symbol: str
    stress: int = 0
    optional: bool = False

    def __str__(self):
        out = self.symbol
        out += Keysymbol.stress_marker(self.stress)
        if self.optional:
            out += "?"

        return out
    
    __repr__ = __str__

    @property
    def is_vowel(self):
        return self.base_symbol in _vowel_symbols

    @property
    def is_consonant(self):
        return self.base_symbol not in _vowel_symbols

    @property
    def base_symbol(self):
        """Strips brackets and digits from a keysymbol"""
        return _KEYSYMBOL_SUB.sub("", self.symbol.lower())


    @staticmethod
    def stress_marker(stress: int):
        if stress <= 0:
            return ""
        return f"!{stress}"



    @staticmethod
    def parse_seq(transcription: str):
        phonetic_keysymbols: list[Keysymbol] = []
        next_stress = 0
        for keysymbol in transcription.split(" "):
            if len(keysymbol) == 0: continue

            if keysymbol in _STRESS_KEYSYMBOLS:
                next_stress = _STRESS_KEYSYMBOLS[keysymbol]

            if any(ch in keysymbol for ch in _NONPHONETIC_KEYSYMBOLS): continue

            optional = keysymbol.startswith("[") and keysymbol.endswith("]")
            phonetic_keysymbols.append(Keysymbol(_KEYSYMBOL_OPTIONAL_SUB.sub("", keysymbol), next_stress, optional))

            next_stress = 0

        return tuple(phonetic_keysymbols)

    @staticmethod
    def max_stress_value(stress_values: Iterable[int]):
        max_stress = 0
        for stress in stress_values:
            if stress == 0: continue

            if max_stress == 0 or stress < max_stress:
                max_stress = stress
        
        return max_stress

    @staticmethod
    def adjust_stress(stress_values: Iterable[int], max_stress: int) -> Generator[int, None, None]:
        for stress in stress_values:
            if stress == 0:
                yield 0
            else:
                yield stress - max_stress + 1

    @staticmethod
    def adjust_keysymbol_stress(keysymbols: "tuple[Keysymbol, ...]", max_stress: int):
        if max_stress == 0:
            return keysymbols

        for keysymbol, stress in zip(keysymbols, Keysymbol.adjust_stress((keysymbol.stress for keysymbol in keysymbols), max_stress)):
            if stress == 0:
                yield keysymbol
            else:
                yield dataclasses.replace(keysymbol, stress=stress)

    
    @staticmethod
    def normalize_stress(keysymbols: "tuple[Keysymbol, ...]") -> "tuple[tuple[Keysymbol, ...], int]":
        max_stress = Keysymbol.max_stress_value(keysymbol.stress for keysymbol in keysymbols)
        new_keysymbols = tuple(Keysymbol.adjust_keysymbol_stress(keysymbols, max_stress))
        return (new_keysymbols, max_stress)