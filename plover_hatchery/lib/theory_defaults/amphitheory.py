from abc import ABC

from plover.steno import Stroke

from ..theory_factory import TheorySpec, TheoryService
from ..sophone.Sophone import Sophone

@TheoryService.theory
class amphitheory(TheorySpec, ABC):
    ALL_KEYS = Stroke.from_steno("@STKPWHRAO*EUFRPBLGTSDZ")


    LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("@STKPWHR")
    VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
    RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")
    ASTERISK_SUBSTROKE = Stroke.from_steno("*")


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
