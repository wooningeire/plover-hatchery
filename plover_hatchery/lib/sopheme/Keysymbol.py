from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Keysymbol:
    symbol: str
    match_symbol: str
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

    @staticmethod
    def get_match_symbol(symbol: str):
        return re.sub(r"[\[\]\d]", "", symbol.lower())