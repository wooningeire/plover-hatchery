from abc import ABC

from plover.steno import Stroke

from ..sophone.Sophone import Sophone
from ..sopheme import Keysymbol, Sopheme, Sound

def _vowel_char_to_steno(char: str):
    return {
        "a": "A",
        "e": "E",
        "i": "EU",
        "o": "O",
        "u": "U",
    }.get(char)

def vowel_to_steno(sound: Sound):
    spelled = _vowel_char_to_steno(sound.sopheme.chars)
    return {
        "e": "E",
        "ao": "A",
        "a": "A",
        "ah": "A",
        "oa": "A",
        "aa": "O",
        "ar": "A",
        "eh": "A",
        "ou": "OE",
        "ouw": "OE",
        "oou": "OE",
        "o": "O",
        "au": "O",
        "oo": "O",
        "or": "O",
        "our": "O",
        "ii": "AOE",
        "iy": "AOE",
        "i": "EU",
        "@r": spelled,
        "@": spelled,
        "uh": "U",
        "u": "U",
        "uu": "AOU",
        "iu": "AOU",
        "ei": "AEU",
        "ee": "AEU",
        "ai": "AOEU",
        "ae": "AOEU",
        "aer": "AOEU",
        "aai": "AOEU",
        "oi": "OEU",
        "oir": "OEU",
        "ow": "OU",
        "owr": "OU",
        "oow": "OU",
        "ir": "AOE",
        "@@r": spelled,
        "er": "E",
        "eir": "E",
        "ur": "U",
        "i@": spelled,
    }[sound.keysymbol.base_symbol]

def vowel_diphthong_transition(vowel: Sound):
    y = Sopheme("", (Keysymbol("y", 0, True),))
    w = Sopheme("", (Keysymbol("w", 0, True),))

    return {
        "E": y,
        "OE": w,
        "OU": w,
        "EU": y,
        "AOE": y,
        "AOU": w,
        "AEU": y,
        "OEU": y,
        "AOEU": y,
    }.get(vowel_to_steno(vowel), None)

class TheorySpec(ABC):
    ALL_KEYS: Stroke


    LEFT_BANK_CONSONANTS_SUBSTROKE: Stroke
    VOWELS_SUBSTROKE: Stroke
    RIGHT_BANK_CONSONANTS_SUBSTROKE: Stroke
    ASTERISK_SUBSTROKE: Stroke


    PHONEMES_TO_CHORDS_LEFT: dict[Sophone, Stroke]
    PHONEMES_TO_CHORDS_VOWELS: dict[Sophone, Stroke]
    PHONEMES_TO_CHORDS_RIGHT: dict[Sophone, Stroke]
    PHONEMES_TO_CHORDS_LEFT_ALT: dict[Sophone, Stroke]
    PHONEMES_TO_CHORDS_RIGHT_ALT: dict[Sophone, Stroke]

    LINKER_CHORD: Stroke
    INITIAL_VOWEL_CHORD: "Stroke | None"

    CYCLER_STROKE: Stroke
    # CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

    PROHIBITED_STROKES: set[Stroke]

    CLUSTERS: dict[tuple[Sophone, ...], Stroke]

    VOWEL_CONSCIOUS_CLUSTERS: "dict[tuple[Sophone | Stroke, ...], Stroke]"


    DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL: dict[Sophone, Sophone]

    class TransitionCosts(ABC):
        VOWEL_ELISION: int
        CLUSTER: int
        ALT_CONSONANT: int


    @staticmethod
    def vowel_to_steno(sound: Sound):
        return vowel_to_steno(sound)
    @staticmethod
    def vowel_diphthong_transition(sound: Sound):
        return vowel_diphthong_transition(sound)