from typing import Iterable, Callable

from plover.steno import Stroke

from ..sopheme import Sound
from ..sophone.Sophone import Sophone


def sophone_mapper(get_sophone_from_sound: Callable[[Sound], Sophone]):
    def map_sophones(mappings: "dict[str, str | Iterable[str]]"):
        chords = {
            Sophone.__dict__[key]: (Stroke.from_steno(steno_or_stenos),)
                if isinstance(steno_or_stenos, str) else
                tuple(Stroke.from_steno(steno) for steno in steno_or_stenos)
            for key, steno_or_stenos in mappings.items()
        }

        def generate(sound: Sound):
            sophone = get_sophone_from_sound(sound)
            if sophone not in chords:
                return
            
            yield from chords[sophone]

        return generate

    return map_sophones


def default_sound_to_sophone_mapping(sound: Sound):
    spelled = {
        "a": Sophone.A,
        "e": Sophone.E,
        "i": Sophone.I,
        "o": Sophone.O,
        "u": Sophone.U,
    }.get(sound.sopheme.chars)

    return {
        "p": (Sophone.P,),
        "t": (Sophone.T, Sophone.D),
        "?": (),  # glottal stop
        "t^": (Sophone.T, Sophone.R),  # tapped R
        "k": (Sophone.K,),
        "x": (Sophone.K,),
        "b": (Sophone.B,),
        "d": (Sophone.D, Sophone.T),
        "g": (Sophone.G,),
        "ch": (Sophone.CH,),
        "jh": (Sophone.J,),
        "s": (Sophone.S,),
        "z": (Sophone.Z,),
        "sh": (Sophone.SH,),
        "zh": (Sophone.SH, Sophone.J),
        "f": (Sophone.F,),
        "v": (Sophone.V,),
        "th": (Sophone.TH,),
        "dh": (Sophone.TH,),
        "h": (Sophone.H,),
        "m": (Sophone.M,),
        "m!": (Sophone.M,),
        "n": (Sophone.N,),
        "n!": (Sophone.N,),
        "ng": (Sophone.NG,),
        "l": (Sophone.L,),
        "ll": (Sophone.L,),
        "lw": (Sophone.L,),
        "l!": (Sophone.L,),
        "r": (Sophone.R,),
        "y": (Sophone.Y,),
        "w": (Sophone.W,),
        "hw": (Sophone.W,),
        
        "e": (Sophone.E, Sophone.EE, Sophone.AA),
        "ao": (Sophone.A, Sophone.AA, Sophone.O, Sophone.U),
        "a": (Sophone.A, Sophone.AA),
        "ah": (Sophone.A, Sophone.O),
        "oa": (Sophone.A, Sophone.O, Sophone.U),
        "aa": (Sophone.O, Sophone.A),
        "ar": (Sophone.A,),
        "eh": (Sophone.A,),
        "ou": (Sophone.OO, Sophone.O),
        "ouw": (Sophone.OO,),
        "oou": (Sophone.OO,),
        "o": (Sophone.O,),
        "au": (Sophone.O, Sophone.A),
        "oo": (Sophone.O,),
        "or": (Sophone.O,),
        "our": (Sophone.O,),
        "ii": (Sophone.EE,),
        "iy": (Sophone.EE,),
        "i": (Sophone.I, Sophone.EE, Sophone.E),
        "@r": (spelled,),
        "@": (spelled,),
        "uh": (Sophone.U,),
        "u": (Sophone.U, Sophone.O, Sophone.OO),
        "uu": (Sophone.UU,),
        "iu": (Sophone.UU,),
        "ei": (Sophone.AA, Sophone.E),
        "ee": (Sophone.AA, Sophone.E, Sophone.A),
        "ai": (Sophone.II,),
        "ae": (Sophone.II,),
        "aer": (Sophone.II,),
        "aai": (Sophone.II,),
        "oi": (Sophone.OI,),
        "oir": (Sophone.OI,),
        "ow": (Sophone.OU,),
        "owr": (Sophone.OU,),
        "oow": (Sophone.OU,),
        "ir": (Sophone.EE,),
        "@@r": (spelled,),
        "er": (Sophone.E, Sophone.U),
        "eir": (Sophone.E,),
        "ur": (Sophone.U, Sophone.UU),
        "i@": (spelled,),
    }[sound.keysymbol.base_symbol][0]