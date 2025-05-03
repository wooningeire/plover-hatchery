from plover_hatchery.lib.pipes import *
from plover_hatchery.lib.pipes.types import Soph

@compile_theory
def theory():
    def map_phonemes(phoneme: SophemeSeqPhoneme):
        as_spelled = ""
        if any(part in phoneme.sopheme.chars for part in ("aw", "au")):
            as_spelled = "AU"
        elif any(part in phoneme.sopheme.chars for part in ("ow", "ou")):
            as_spelled = "OU"
        elif any(part in phoneme.sopheme.chars for part in ("oi", "oy")):
            as_spelled = "OI"
        elif any(part in phoneme.sopheme.chars for part in ("ew",)):
            as_spelled = "UU"
        elif any(part in phoneme.sopheme.chars for part in ("ei",)):
            as_spelled = "E"
        elif any(part in phoneme.sopheme.chars for part in ("a",)):
            as_spelled = "A AA"
        elif any(part in phoneme.sopheme.chars for part in ("e",)):
            as_spelled = "E EE"
        elif any(part in phoneme.sopheme.chars for part in ("i",)):
            as_spelled = "I II"
        elif any(part in phoneme.sopheme.chars for part in ("o",)):
            as_spelled = "O OO"
        elif any(part in phoneme.sopheme.chars for part in ("u",)):
            as_spelled = "U UU"

        mapping = {
            "p": "P",
            "t": "T",
            "?": "",  # glottal stop
            "t^": "T",  # tapped R
            "k": "K",
            "x": "K",
            "b": "B",
            "d": "D",
            "g": "G",
            "ch": "CH",
            "jh": "J",
            "s": "S",
            "z": "Z",
            "sh": "SH",
            "zh": "SH J",
            "f": "F",
            "v": "V",
            "th": "TH",
            "dh": "TH",
            "h": "H",
            "m": "M",
            "m!": "M",
            "n": "N",
            "n!": "N",
            "ng": "NG",
            "l": "L",
            "ll": "L",
            "lw": "L",
            "l!": "L",
            "r": "R",
            "y": "Y",
            "w": "W",
            "hw": "W",
            
            "e": "E",
            "ao": "A",
            "a": "A",
            "ah": "A",
            "oa": "A",
            "aa": "O",
            "ar": "A",
            "eh": "A",
            "ou": "OO",
            "ouw": "OO",
            "oou": "OO",
            "o": "O",
            "au": "O",
            "oo": "O",
            "or": "O",
            "our": "O",
            "ii": "EE",
            "iy": "EE",
            "i": "I",
            "@r": as_spelled,
            "@": as_spelled,
            "uh": "U",
            "u": "U",
            "uu": "UU",
            "iu": "UU",
            "ei": "AA E",
            "ee": "AA",
            "ai": "II",
            "ae": "II",
            "aer": "II",
            "aai": "II",
            "oi": "OI",
            "oir": "OI",
            "ow": "OU",
            "owr": "OU",
            "oow": "OU",
            "ir": "EE",
            "@@r": as_spelled,
            "er": "E",
            "eir": "AA E",
            "ur": "U",
            "i@": as_spelled,
        }

        return (Soph(value) for value in mapping.get(phoneme.keysymbol.symbol, phoneme.keysymbol.symbol).split())


    yield soph_trie(map_phonemes, {
        "A": "A",
        "B": "PW -B",
        "CH": "KH -FP",
        "D": "TK -D",
        "F": "TP -F",
        "G": "TKPW -G",
        "H": "H",
        "J": "SKWR -PBLG",
        "M": "PH -PL",
        "N": "TPH -PB",
        "NG": "TPH -PBG",
        "K": "K -BG",
        "L": "HR -L",
        "P": "P -P",
        "R": "R -R",
        "S": "S -S",
        "SH": "SH -RB",
        "T": "T -T",
        "TH": "TH *T",
        "W": "W",
        "V": "SR -FB",
        "Y": "KWR",
        "Z": "STKPW -Z",
        "ZH": "STKPWH *RB",

        "AA": "AEU",
        "A": "A",
        "EE": "AOE",
        "E": "E",
        "II": "AOEU",
        "I": "EU",
        "OO": "OE",
        "O": "O",
        "UU": "AOU",
        "U": "U",
        "AU": "AU",
        "OI": "OEU",
        "OU": "OU",
    })