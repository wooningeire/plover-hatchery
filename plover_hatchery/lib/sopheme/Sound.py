from dataclasses import dataclass

from .Steneme import Steneme
from ..stenophoneme.Stenophoneme import Stenophoneme

@dataclass
class Sound:
    phoneme: Stenophoneme
    steneme: "Steneme | None"

    @staticmethod
    def from_sopheme(steneme: Steneme):
        assert steneme.phoneme is not None
        return Sound(steneme.phoneme, steneme)