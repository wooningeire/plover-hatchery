from dataclasses import dataclass

from .Keysymbol import Keysymbol
from .Sopheme import Sopheme

@dataclass(frozen=True)
class Sound:
    keysymbol: Keysymbol
    sopheme: Sopheme
