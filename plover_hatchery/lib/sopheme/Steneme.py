
from dataclasses import dataclass
from typing import Iterable

from plover.steno import Stroke

from ..stenophoneme.Stenophoneme import Stenophoneme
from .Keysymbol import Keysymbol
from .Sopheme import Sopheme


@dataclass(frozen=True)
class Steneme:
    sophemes: tuple[Sopheme, ...]
    steno: tuple[Stroke, ...]
    phoneme: "Stenophoneme | None"

    def __str__(self):
        out = " ".join(str(sopheme) for sopheme in self.sophemes)
        if len(self.sophemes) > 1 and (self.phoneme is not None or len(self.steno) > 0):
            out = f"({out})"

        if self.phoneme is not None:
            out += f"[{self.phoneme}]"
        elif len(self.steno) > 0:
            out += f"[[{'/'.join(stroke.rtfcre for stroke in self.steno)}]]"
            
        return out
    
    __repr__ = __str__

    def shortest_form(self):
        key = (
            tuple(
                (
                    tuple(keysymbol.symbol for keysymbol in sopheme.keysymbols),
                    sopheme.chars,
                )
                for sopheme in self.sophemes
            ),
            self.phoneme,
        )

        return _steneme_shorthands.get(key, str(self))
    
    def to_dict(self):
        return {
            "orthokeysymbols": [
                {
                    "chars": sopheme.chars,
                    "keysymbols": [
                        {
                            "symbol": keysymbol.symbol,
                            "stress": keysymbol.stress,
                            "optional": keysymbol.optional,
                        }
                        for keysymbol in sopheme.keysymbols
                    ],
                }
                for sopheme in self.sophemes
            ],
            "steno": "/".join(stroke.rtfcre for stroke in self.steno),
            "phono": self.phoneme.name if isinstance(self.phoneme, Stenophoneme) else self.phoneme,
        }

    @staticmethod
    def parse_sopheme_dict(json: dict):
        return Steneme(
            tuple(
                Sopheme(
                    sophemes_json["chars"],
                    tuple(
                        Keysymbol(
                            keysymbol_json["symbol"],
                            Keysymbol.get_match_symbol(keysymbol_json["symbol"]),
                            keysymbol_json["stress"],
                            keysymbol_json["optional"],
                        )
                        for keysymbol_json in sophemes_json["keysymbols"]
                    ),
                )
                for sophemes_json in json["orthokeysymbols"]
            ),
            tuple(Stroke.from_steno(steno) for steno in json["steno"].split("/")) if len(json["steno"]) > 0 else (),
            Stenophoneme.__dict__.get(json["phono"], json["phono"]),  
        )
    
    @staticmethod
    def get_translation(stenemes: "Iterable[Steneme]"):
        return "".join(
            sopheme.chars
            for steneme in stenemes
            for sopheme in steneme.sophemes
        )


_steneme_shorthands = {
    ((((keysymbols), ortho),), phoneme): ortho
    for (phoneme, keysymbols), orthos in {
        (Stenophoneme.P, ("p",)): ("p", "pp"),
        (Stenophoneme.T, ("t",)): ("t", "tt"),
        (Stenophoneme.K, ("k",)): ("k", "kk", "ck", "q"),
        (Stenophoneme.B, ("b",)): ("b", "bb"),
        (Stenophoneme.D, ("d",)): ("d", "dd"),
        (Stenophoneme.G, ("g",)): ("g", "gg"),
        (Stenophoneme.CH, ("ch",)): ("ch",),
        (Stenophoneme.J, ("jh",)): ("j",),
        (Stenophoneme.S, ("s",)): ("s", "ss"),
        (Stenophoneme.Z, ("z",)): ("z", "zz"),
        (Stenophoneme.SH, ("sh",)): ("sh", "ti", "ci", "si", "ssi"),
        (Stenophoneme.F, ("f",)): ("f", "ff", "ph"),
        (Stenophoneme.V, ("v",)): ("v", "vv"),
        (Stenophoneme.H, ("h",)): ("h",),
        (Stenophoneme.M, ("m",)): ("m", "mm"),
        (Stenophoneme.N, ("n",)): ("n", "nn"),
        (Stenophoneme.L, ("l",)): ("l", "ll"),
        (Stenophoneme.R, ("r",)): ("r", "rr"),
        (Stenophoneme.Y, ("y",)): ("y",),
        (Stenophoneme.W, ("w",)): ("w",),
    }.items()
    for ortho in orthos
}