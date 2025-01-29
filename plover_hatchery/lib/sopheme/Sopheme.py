from dataclasses import dataclass
from typing import Iterable

from plover.steno import Stroke

from ..stenophoneme.Stenophoneme import Stenophoneme
from .Keysymbol import Keysymbol


@dataclass(frozen=True)
class Sopheme:
    chars: str
    keysymbols: tuple[Keysymbol, ...]

    def __str__(self):
        keysymbols_string = " ".join(str(keysymbol) for keysymbol in self.keysymbols)
        if len(self.keysymbols) > 1:
            keysymbols_string = f"({keysymbols_string})"

        return f"{self.chars}.{keysymbols_string}"
    
    __repr__ = __str__

    @staticmethod
    def format_seq(sophemes: "Iterable[Sopheme]"):
        return " ".join(str(sopheme) for sopheme in sophemes)
