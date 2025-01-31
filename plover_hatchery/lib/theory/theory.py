from abc import ABC

from plover.steno import Stroke

from .spec import TheorySpec
from .service import TheoryService

from ..stenophoneme.Stenophoneme import Sophone
from ..sopheme import Sound, Sopheme, Keysymbol

@TheoryService.theory
class amphitheory(TheorySpec, ABC):
    ALL_KEYS = Stroke.from_steno("@STKPWHRAO*EUFRPBLGTSDZ")


    LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("@STKPWHR")
    VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
    RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")
    ASTERISK_SUBSTROKE = Stroke.from_steno("*")


    PHONEMES_TO_CHORDS_LEFT: dict[Sophone, Stroke] = {
        phoneme: Stroke.from_steno(steno)
        for phoneme, steno in {
            Sophone.S: "S",
            Sophone.T: "T",
            Sophone.K: "K",
            Sophone.P: "P",
            Sophone.W: "W",
            Sophone.H: "H",
            Sophone.R: "R",

            Sophone.Z: "STKPW",
            Sophone.J: "SKWR",
            Sophone.V: "SR",
            Sophone.D: "TK",
            Sophone.G: "TKPW",
            Sophone.F: "TP",
            Sophone.N: "TPH",
            Sophone.Y: "KWR",
            Sophone.B: "PW",
            Sophone.M: "PH",
            Sophone.L: "HR",

            Sophone.SH: "SH",
            Sophone.TH: "TH",
            Sophone.CH: "KH",

            Sophone.NG: "TPH",
        }.items()
    }

    PHONEMES_TO_CHORDS_VOWELS: dict[Sophone, Stroke] = {
        phoneme: Stroke.from_steno(steno)
        for phoneme, steno in {
            Sophone.AA: "AEU",
            Sophone.A: "A",
            Sophone.EE: "AOE",
            Sophone.E: "E",
            Sophone.II: "AOEU",
            Sophone.I: "EU",
            Sophone.OO: "OE",
            Sophone.O: "O",
            Sophone.UU: "AOU",
            Sophone.U: "U",
            Sophone.AU: "AU",
            Sophone.OI: "OEU",
            Sophone.OU: "OU",
            Sophone.AE: "AE",
            Sophone.AO: "AO",
        }.items()
    }

    PHONEMES_TO_CHORDS_RIGHT: dict[Sophone, Stroke] = {
        phoneme: Stroke.from_steno(steno)
        for phoneme, steno in {
            Sophone.DUMMY: "",

            Sophone.F: "-F",
            Sophone.R: "-R",
            Sophone.P: "-P",
            Sophone.B: "-B",
            Sophone.L: "-L",
            Sophone.G: "-G",
            Sophone.T: "-T",
            Sophone.S: "-S",
            Sophone.D: "-D",
            Sophone.Z: "-Z",

            Sophone.V: "-FB",
            Sophone.N: "-PB",
            Sophone.M: "-PL",
            Sophone.K: "-BG",
            Sophone.J: "-PBLG",
            Sophone.CH: "-FP",
            Sophone.SH: "-RB",
            Sophone.TH: "*T",
        }.items()

        # "SHR": "shr",
        # "THR": "thr",
        # "KHR": "chr",
        # "-FRP": (Phoneme.M, Phoneme.P),
        # "-FRB": (Phoneme.R, Phoneme.V),
    }


    PHONEMES_TO_CHORDS_LEFT_ALT: dict[Sophone, Stroke] = {
        phoneme: Stroke.from_steno(steno)
        for phoneme, steno in {
            Sophone.F: "W",
            Sophone.V: "W",
            Sophone.Z: "S*",
        }.items()
    }

    PHONEMES_TO_CHORDS_RIGHT_ALT: dict[Sophone, Stroke] = {
        phoneme: Stroke.from_steno(steno)
        for phoneme, steno in {
            Sophone.S: "-F",
            Sophone.Z: "-F",
            Sophone.V: "-F",
            Sophone.TH: "-F",
            Sophone.M: "-FR",
            Sophone.J: "-FR",
            Sophone.K: "*G",
        }.items()
    }

    LINKER_CHORD = Stroke.from_steno("SWH")
    INITIAL_VOWEL_CHORD = Stroke.from_steno("@")

    CYCLER_STROKE = Stroke.from_steno("@")
    # CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

    PROHIBITED_STROKES = {
        Stroke.from_steno(steno)
        for steno in ("AEU",)
    }

    CLUSTERS: dict[tuple[Sophone, ...], Stroke] = {
        phonemes: Stroke.from_steno(steno)
        for phonemes, steno in {
            (Sophone.D, Sophone.S): "STK",
            (Sophone.D, Sophone.S, Sophone.T): "STK",
            (Sophone.D, Sophone.S, Sophone.K): "STK",
            (Sophone.K, Sophone.N): "K",
            (Sophone.K, Sophone.M, Sophone.P): "KP",
            (Sophone.K, Sophone.M, Sophone.B): "KPW",
            (Sophone.L, Sophone.F): "-FL",
            (Sophone.L, Sophone.V): "-FL",
            (Sophone.G, Sophone.L): "-LG",
            (Sophone.L, Sophone.J): "-LG",
            (Sophone.K, Sophone.L): "*LG",
            (Sophone.N, Sophone.J): "-PBG",
            (Sophone.M, Sophone.J): "-PLG",
            (Sophone.R, Sophone.F): "*FR",
            (Sophone.R, Sophone.S): "*FR",
            (Sophone.R, Sophone.M): "*FR",
            (Sophone.R, Sophone.V): "-FRB",
            (Sophone.L, Sophone.CH): "-LG",
            (Sophone.R, Sophone.CH): "-FRPB",
            (Sophone.N, Sophone.CH): "-FRPBLG",
            (Sophone.L, Sophone.SH): "*RB",
            (Sophone.R, Sophone.SH): "*RB",
            (Sophone.N, Sophone.SH): "*RB",
            (Sophone.M, Sophone.P): "*PL",
            (Sophone.T, Sophone.L): "-LT",
        }.items()
    }

    VOWEL_CONSCIOUS_CLUSTERS: "dict[tuple[Sophone | Stroke, ...], Stroke]" = {
        tuple(
            Stroke.from_steno(phoneme) if isinstance(phoneme, str) else phoneme
            for phoneme in phonemes
        ): Stroke.from_steno(steno)
        for phonemes, steno in {
            (Sophone.ANY_VOWEL, Sophone.N, Sophone.T): "SPW",
            (Sophone.ANY_VOWEL, Sophone.N, Sophone.D): "SPW",
            (Sophone.ANY_VOWEL, Sophone.M, Sophone.P): "KPW",
            (Sophone.ANY_VOWEL, Sophone.M, Sophone.B): "KPW",
            (Sophone.ANY_VOWEL, Sophone.N, Sophone.K): "SKPW",
            (Sophone.ANY_VOWEL, Sophone.N, Sophone.G): "SKPW",
            (Sophone.ANY_VOWEL, Sophone.N, Sophone.J): "SKPW",
            (Sophone.E, Sophone.K, Sophone.S): "SKW",
            (Sophone.E, Sophone.K, Sophone.S, Sophone.T): "STKW",
            (Sophone.E, Sophone.K, Sophone.S, Sophone.K): "SKW",
            (Sophone.E, Sophone.K, Sophone.S, Sophone.P): "SKPW",
            (Sophone.ANY_VOWEL, Sophone.N): "TPH",
            (Sophone.ANY_VOWEL, Sophone.N, Sophone.S): "STPH",
            (Sophone.ANY_VOWEL, Sophone.N, Sophone.F): "TPW",
            (Sophone.ANY_VOWEL, Sophone.N, Sophone.V): "TPW",
            (Sophone.ANY_VOWEL, Sophone.M): "PH",
        }.items()
    }


    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL: dict[Sophone, Sophone] = {
        prev_vowel_phoneme: phoneme
        for prev_vowel_phoneme, phoneme in {
            Sophone.E: Sophone.Y,
            Sophone.OO: Sophone.W,
            Sophone.OU: Sophone.W,
            Sophone.I: Sophone.Y,
            Sophone.EE: Sophone.Y,
            Sophone.UU: Sophone.W,
            Sophone.AA: Sophone.Y,
            Sophone.OI: Sophone.Y,
            Sophone.II: Sophone.Y,
        }.items()
    }

    class TransitionCosts(TheorySpec.TransitionCosts, ABC):
        VOWEL_ELISION = 5
        CLUSTER = 2
        ALT_CONSONANT = 3