from abc import ABC

from plover.steno import Stroke

from ..theory_factory import TheorySpec, TheoryService
from ..sophone.Sophone import Sophone

@TheoryService.theory
class lapwing(TheorySpec, ABC):
    ALL_KEYS = Stroke.from_steno("STKPWHRAO*EUFRPBLGTSDZ")


    LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR")
    VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
    RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")
    ASTERISK_SUBSTROKE = Stroke.from_steno("*")

    PHONEMES_TO_CHORDS_LEFT = {
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

    PHONEMES_TO_CHORDS_VOWELS = {
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

    LINKER_CHORD = Stroke.from_steno("KWR")
    INITIAL_VOWEL_CHORD = None

    CYCLER_STROKE = Stroke.from_steno("#TPHEGT")
    # CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

    PROHIBITED_STROKES = set()

    CLUSTERS = {}

    VOWEL_CONSCIOUS_CLUSTERS = {}


    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL = {}

    class TransitionCosts(TheorySpec.TransitionCosts, ABC):
        VOWEL_ELISION = 0
        CLUSTER = 0
        ALT_CONSONANT = 0

