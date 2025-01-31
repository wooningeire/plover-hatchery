
from dataclasses import dataclass
from typing import Iterable

from plover.steno import Stroke

from ..stenophoneme.Stenophoneme import Sophone
from .Keysymbol import Keysymbol
from .Sopheme import Sopheme


@dataclass(frozen=True)
class Steneme:
    sophemes: tuple[Sopheme, ...]
    steno: tuple[Stroke, ...]
    phoneme: "Sophone | None"

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
            "phono": self.phoneme.name if isinstance(self.phoneme, Sophone) else self.phoneme,
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
                            keysymbol_json["stress"],
                            keysymbol_json["optional"],
                        )
                        for keysymbol_json in sophemes_json["keysymbols"]
                    ),
                )
                for sophemes_json in json["orthokeysymbols"]
            ),
            tuple(Stroke.from_steno(steno) for steno in json["steno"].split("/")) if len(json["steno"]) > 0 else (),
            Sophone.__dict__.get(json["phono"], json["phono"]),  
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
        (Sophone.P, ("p",)): ("p", "pp"),
        (Sophone.T, ("t",)): ("t", "tt"),
        (Sophone.K, ("k",)): ("k", "kk", "ck", "q"),
        (Sophone.B, ("b",)): ("b", "bb"),
        (Sophone.D, ("d",)): ("d", "dd"),
        (Sophone.G, ("g",)): ("g", "gg"),
        (Sophone.CH, ("ch",)): ("ch",),
        (Sophone.J, ("jh",)): ("j",),
        (Sophone.S, ("s",)): ("s", "ss"),
        (Sophone.Z, ("z",)): ("z", "zz"),
        (Sophone.SH, ("sh",)): ("sh", "ti", "ci", "si", "ssi"),
        (Sophone.F, ("f",)): ("f", "ff", "ph"),
        (Sophone.V, ("v",)): ("v", "vv"),
        (Sophone.H, ("h",)): ("h",),
        (Sophone.M, ("m",)): ("m", "mm"),
        (Sophone.N, ("n",)): ("n", "nn"),
        (Sophone.L, ("l",)): ("l", "ll"),
        (Sophone.R, ("r",)): ("r", "rr"),
        (Sophone.Y, ("y",)): ("y",),
        (Sophone.W, ("w",)): ("w",),
    }.items()
    for ortho in orthos
}