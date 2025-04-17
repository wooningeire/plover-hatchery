from dataclasses import dataclass
import re


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

keysymbol_sub = re.compile(r"[\[\]\d]")

@dataclass(frozen=True)
class Keysymbol:
    symbol: str
    stress: int = 0
    optional: bool = False

    def __str__(self):
        out = self.symbol
        if self.stress > 0:
            out += f"!{self.stress}"
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
        return keysymbol_sub.sub("", self.symbol.lower())