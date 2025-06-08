from dataclasses import dataclass
from abc import ABC
from typing import NamedTuple, cast
from itertools import cycle
import re

from plover.steno import Stroke

from ..sophone.Sophone import Sophone
from ..sopheme.Keysymbol import Keysymbol
from ..sopheme.Steneme import Steneme
from .steno_annotations import AsteriskableKey, AnnotatedChord
from .alignment import AlignmentService, Cell, Comparable, aligner

from plover_hatchery_lib_rs import Sopheme


_KEYSYMBOL_TO_GRAPHEME_MAPPINGS = {
    tuple(keysymbol.split(" ")): graphemes
    for keysymbol, graphemes in {
        "p": ("p", "pp"),
        "t": ("t", "tt", "d", "dd"),
        "?": (),  # glottal stop
        "t^": ("r", "rr"),  # tapped R
        "k": ("k", "kk", "c", "ck", "cc", "q", "cq"),
        "x": ("k", "kk", "c", "ck", "cc", "q", "cq"),
        "b": ("b", "bb"),
        "d": ("d", "dd", "t", "tt"),
        "g": ("g", "gg"),
        "ch": ("ch", "t", "tt"),
        "jh": ("j", "g"),
        "s": ("s", "ss", "c", "sc", "z", "zz"),
        "z": ("z", "zz", "s", "ss", "x"),
        "sh": ("sh", "ti", "ci", "si", "ssi", "t"),
        "zh": ("sh", "zh", "j", "g", "si", "ssi", "ti", "ci"),
        "f": ("f", "ph", "ff", "v", "vv"),
        "v": ("v", "vv", "f", "ff", "ph"),
        "th": ("th",),
        "dh": ("th",),
        "h": ("h",),
        "m": ("m", "mm"),
        "m!": ("m", "mm"),
        "n": ("n", "nn"),
        "n!": ("n", "nn"),
        "ng": ("n", "ng"),
        "l": ("l", "ll"),
        "ll": ("l", "ll"),
        "lw": ("l", "ll"),
        "l!": ("l", "ll"),
        "r": ("r", "rr"),
        "y": ("y",),
        "w": ("w",),
        "hw": ("w", "wh"),

        "e": ("e", "ea"),
        "ao": ("a",),
        "a": ("a", "aa"),
        "ah": ("a",),
        "oa": ("a",),
        "aa": ("a", "au", "aw"),
        "ar": ("a", "aa"),
        "eh": ("a",),
        "ou": ("o", "oe", "oa", "ou", "ow"),
        "ouw": ("o", "oe", "oa", "ou", "ow"),
        "oou": ("o", "oe", "oa", "ou", "ow"),
        "o": ("o", "a", "ou", "au", "ow", "aw"),
        "au": ("o", "a", "ou", "au", "ow", "aw"),
        "oo": ("o", "a", "ou", "au", "ow", "aw"),
        "or": ("o", "a", "ou", "au", "ow", "aw"),
        "our": ("o", "a", "ou", "au", "ow", "aw"),
        "ii": ("e", "i", "ee", "ea", "ie", "ei"),
        "iy": ("i", "y", "ey", "ei", "ie"),
        "i": ("i", "y"),
        "@r": ("a", "o", "e", "u", "i", "y", "au", "ou"),
        "@": ("a", "o", "e", "u", "i", "y", "au", "ou"),
        "uh": ("u",),
        "u": ("u", "o", "oo"),
        "uu": ("u", "uu", "oo", "ew", "eu"),
        "iu": ("u", "uu", "oo", "ew", "eu"),
        "ei": ("ai", "ei", "a", "e"),
        "ee": ("ai", "ei", "a", "e"),
        "ai": ("i", "ie", "y", "ye"),
        "ae": ("i", "ie", "y", "ye"),
        "aer": ("i", "ie", "y", "ye"),
        "aai": ("i", "ie", "y", "ye"),
        "oi": ("oi", "oy"),
        "oir": ("oi", "oy"),
        "ow": ("ou", "ow", "ao"),
        "owr": ("ou", "ow", "ao"),
        "oow": ("ou", "ow", "ao"),
        "ir": ("e", "ee", "ea", "ie", "ei", "i", "y", "ey"),
        "@@r": ("a", "e", "i", "o", "u", "y", "au", "ou"),
        "er": ("e",),
        "eir": ("ai", "ei", "a", "e"),
        "ur": ("u", "o", "oo"),
        "i@": ("ia", "ie", "io", "iu"),

        "t s": ("z",),
        "d z": ("z",),
        "k s": ("x",),
        "g z": ("x",),
    }.items()
}


_PHONEME_TO_STENO_MAPPINGS = {
    Sophone.B: ("PW", "-B"),
    Sophone.D: ("TK", "-D"),
    Sophone.F: ("TP", "-F"),
    Sophone.G: ("SKWR", "TKPW", "-PBLG", "-G"),
    Sophone.H: ("H",),
    Sophone.J: ("SKWR", "-PBLG", "-G"),
    Sophone.K: ("K", "-BG", "*G"),
    Sophone.L: ("HR", "-L"),
    Sophone.M: ("PH", "-PL"),
    Sophone.N: ("TPH", "-PB"),
    Sophone.P: ("P", "-P"),
    Sophone.R: ("R", "-R"),
    Sophone.S: ("S", "-S", "-F", "-Z", "KR"),
    Sophone.T: ("T", "-T", "SH", "-RB", "KH", "-FP"),
    Sophone.V: ("SR", "-F"),
    Sophone.W: ("W", "U"),
    Sophone.Y: ("KWH", "KWR"),
    Sophone.Z: ("STKPW", "-Z", "-F", "S", "-S", "KP"),

    Sophone.TH: ("TH", "*T"),
    Sophone.SH: ("SH", "-RB"),
    Sophone.CH: ("KH", "-FP"),

    Sophone.NG: ("-PB", "-PBG"),

    Sophone.AA: ("AEU", "AE"),
    Sophone.A: ("A", "AE"),
    Sophone.EE: ("AOE", "EU"),
    Sophone.E: ("E", "AEU"),
    Sophone.II: ("AOEU",),
    Sophone.I: ("EU",),
    Sophone.OO: ("OE", "AU",),
    Sophone.O: ("AU", "O"),
    Sophone.UU: ("AOU", "AO"),
    Sophone.U: ("U", "AO"),
    Sophone.OI: ("OEU",),
    Sophone.OU: ("OU", "AO"),
}

@dataclass(frozen=True)
class _Mapping:
    phoneme: Sophone | None
    keys: tuple[AsteriskableKey, ...]

_mappings = lambda phoneme: tuple(zip(cycle((phoneme,)), _PHONEME_TO_STENO_MAPPINGS[phoneme]))
_vowels = lambda *phonemes: tuple(zip(phonemes, phonemes))
_no_phoneme = lambda *stenos: tuple(zip(cycle((None,)), stenos))

_any_vowel_mapping = (
    (Sophone.A, "A"),
    (Sophone.O, "O"),
    (Sophone.E, "E"),
    (Sophone.U, "U"),
    (Sophone.U, "AO"),
    (Sophone.AA, "AE"),
    (Sophone.AU, "AU"),
    (Sophone.OO, "OE"),
    (Sophone.OU, "OU"),
    (Sophone.I, "EU"),
    (Sophone.EE, "AOE"),
    (Sophone.UU, "AOU"),
    (Sophone.AA, "AEU"),
    (Sophone.OI, "OEU"),
    (Sophone.II, "AOEU"),
)

_KEYSYMBOL_TO_STENO_MAPPINGS = {
    tuple(keysymbol.split(" ")): tuple(_Mapping(phoneme, AsteriskableKey.annotations_from_outline(outline_steno)) for phoneme, outline_steno in mapping)
    for keysymbol, mapping in cast("dict[str, tuple[tuple[Sophone | None, str], ...]]", {
        # How does each keysymbol appear as it does in Lapwing?

        "": _no_phoneme("KWR", "W"),

        "p": _mappings(Sophone.P),
        "t": (*_mappings(Sophone.T), *_mappings(Sophone.D)),
        "?": (),  # glottal stop
        "t^": (*_mappings(Sophone.T), *_mappings(Sophone.R)),  # tapped R
        "k": _mappings(Sophone.K),
        "x": _mappings(Sophone.K),
        "b": _mappings(Sophone.B),
        "d": (*_mappings(Sophone.D), *_mappings(Sophone.T)),
        "g": _mappings(Sophone.G),
        "ch": _mappings(Sophone.CH),
        "jh": _mappings(Sophone.J),
        "s": _mappings(Sophone.S),
        "z": _mappings(Sophone.Z),
        "sh": _mappings(Sophone.SH),
        "zh": (*_mappings(Sophone.SH), *_mappings(Sophone.J)),
        "f": _mappings(Sophone.F),
        "v": _mappings(Sophone.V),
        "th": _mappings(Sophone.TH),
        "dh": _mappings(Sophone.TH),
        "h": _mappings(Sophone.H),
        "m": _mappings(Sophone.M),
        "m!": _mappings(Sophone.M),
        "n": _mappings(Sophone.N),
        "n!": _mappings(Sophone.N),
        "ng": _mappings(Sophone.NG),
        "l": _mappings(Sophone.L),
        "ll": _mappings(Sophone.L),
        "lw": _mappings(Sophone.L),
        "l!": _mappings(Sophone.L),
        "r": _mappings(Sophone.R),
        "y": _mappings(Sophone.Y),
        "w": _mappings(Sophone.W),
        "hw": _mappings(Sophone.W),

        "e": (*_mappings(Sophone.E), *_mappings(Sophone.EE), *_mappings(Sophone.AA)),
        "ao": (*_mappings(Sophone.A), *_mappings(Sophone.AA), *_mappings(Sophone.O), *_mappings(Sophone.U)),
        "a": (*_mappings(Sophone.A), *_mappings(Sophone.AA)),
        "ah": (*_mappings(Sophone.A), *_mappings(Sophone.O)),
        "oa": (*_mappings(Sophone.A), *_mappings(Sophone.O), *_mappings(Sophone.U)),
        "aa": (*_mappings(Sophone.O), *_mappings(Sophone.A)),
        "ar": _mappings(Sophone.A),
        "eh": _mappings(Sophone.A),
        "ou": (*_mappings(Sophone.OO), *_mappings(Sophone.O)),
        "ouw": _mappings(Sophone.OO),
        "oou": _mappings(Sophone.OO),
        "o": _mappings(Sophone.O),
        "au": (*_mappings(Sophone.O), *_mappings(Sophone.A)),
        "oo": _mappings(Sophone.O),
        "or": _mappings(Sophone.O),
        "our": _mappings(Sophone.O),
        "ii": _mappings(Sophone.EE),
        "iy": _mappings(Sophone.EE),
        "i": (*_mappings(Sophone.I), *_mappings(Sophone.EE), *_mappings(Sophone.E)),
        "@r": _any_vowel_mapping,
        "@": _any_vowel_mapping,
        "uh": _mappings(Sophone.U),
        "u": (*_mappings(Sophone.U), *_mappings(Sophone.O), *_mappings(Sophone.OO)),
        "uu": _mappings(Sophone.UU),
        "iu": _mappings(Sophone.UU),
        "ei": (*_mappings(Sophone.AA), *_mappings(Sophone.E)),
        "ee": (*_mappings(Sophone.AA), *_mappings(Sophone.E), *_mappings(Sophone.A)),
        "ai": _mappings(Sophone.II),
        "ae": _mappings(Sophone.II),
        "aer": _mappings(Sophone.II),
        "aai": _mappings(Sophone.II),
        "oi": _mappings(Sophone.OI),
        "oir": _mappings(Sophone.OI),
        "ow": _mappings(Sophone.OU),
        "owr": _mappings(Sophone.OU),
        "oow": _mappings(Sophone.OU),
        "ir": _mappings(Sophone.EE),
        "@@r": _any_vowel_mapping,
        "er": (*_mappings(Sophone.E), *_mappings(Sophone.U)),
        "eir": _mappings(Sophone.E),
        "ur": (*_mappings(Sophone.U), *_mappings(Sophone.UU)),
        "i@": _any_vowel_mapping,
        
        "k s": _no_phoneme("KP"),
        "g z": _no_phoneme("KP"),
        "sh n": _no_phoneme("-GS"),
        "zh n": _no_phoneme("-GS"),
        "k sh n": _no_phoneme("-BGS"),
        "k zh n": _no_phoneme("-BGS"),
        "m p": _no_phoneme("*PL"),
        "y uu": _mappings(Sophone.UU),
    }).items()
}

class _Cost(NamedTuple):
    n_unmatched_keysymbols: int
    n_unmatched_chars: int
    n_chunks: int


@aligner
class match_keysymbols_to_chars(
    AlignmentService[
        _Cost,
        None,
        tuple[Keysymbol, ...],
        str,
        str,
        str,
        Keysymbol,
        str,
        Sopheme,
    ],
    ABC,
):

    @staticmethod
    def process_input(transcription: tuple[Keysymbol, ...], translation: str) -> tuple[tuple[Keysymbol, ...], str]:
        return (transcription, translation)
    
    @staticmethod
    def initial_cost():
        return _Cost(0, 0, 0)
    
    @staticmethod
    def mismatch_cost(mismatch_parent: Cell[_Cost, None], increment_x: bool, increment_y: bool):
        return _Cost(
            mismatch_parent.cost.n_unmatched_keysymbols + (1 if increment_x else 0),
            mismatch_parent.cost.n_unmatched_chars + (1 if increment_y else 0),
            mismatch_parent.cost.n_chunks + 1 if mismatch_parent.has_match else mismatch_parent.cost.n_chunks,
        )
    
    @staticmethod
    def generate_candidate_x_key(candidate_subseq_x: tuple[Keysymbol, ...]) -> tuple[str, ...]:
        return tuple(keysymbol.base_symbol for keysymbol in candidate_subseq_x)
    
    @staticmethod
    def has_mapping(candidate_x_key: tuple[str, ...]):
        return candidate_x_key in _KEYSYMBOL_TO_GRAPHEME_MAPPINGS
    
    @staticmethod
    def get_mapping_options(candidate_x_key: tuple[str, ...]):
        return _KEYSYMBOL_TO_GRAPHEME_MAPPINGS[candidate_x_key]
        
    @staticmethod
    def is_match(actual_chars: str, candidate_chars: str):
        return actual_chars == candidate_chars
    
    @staticmethod
    def match_cost(parent: Cell[_Cost, None]):
        return _Cost(
            parent.cost.n_unmatched_keysymbols,
            parent.cost.n_unmatched_chars,
            parent.cost.n_chunks + 1,
        )
    
    @staticmethod
    def match_data(subseq_keysymbols: tuple[Keysymbol, ...], subseq_chars: str, pre_subseq_keysymbols: tuple[str, ...], pre_subseq_chars: str):
        return None

    @staticmethod
    def construct_match(keysymbols: tuple[Keysymbol, ...], translation: str, start_cell: Cell[_Cost, None], end_cell: Cell[_Cost, None], _: None):
        return Sopheme(
            translation[start_cell.y:end_cell.y],
            keysymbols[start_cell.x:end_cell.x],
        )
