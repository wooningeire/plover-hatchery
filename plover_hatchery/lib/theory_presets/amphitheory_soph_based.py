from plover_hatchery.lib.pipes import *
from plover_hatchery.lib.sopheme.parse.parse_sopheme_sequence import parse_sopheme_seq

@compile_theory
def theory():
    yield floating_keys("*")


    def map_phoneme_to_sophs(phoneme: SophemeSeqPhoneme):
        as_spelled = ""
        if any(part in phoneme.sopheme.chars for part in ("aw", "au")):
            as_spelled = "AU"
        elif any(part in phoneme.sopheme.chars for part in ("ow", "ou")):
            as_spelled = "OU"
        elif any(part in phoneme.sopheme.chars for part in ("oi", "oy")):
            as_spelled = "OI"
        elif any(part in phoneme.sopheme.chars for part in ("ai", "ay")):
            as_spelled = "AA"
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


    sophs_to_main_chords = {
        "B": "PW -B",
        "CH": "KH -FP",
        "D": "TK -D",
        "F": "TP -F",
        "G": "TKPW -G",
        "H": "H",
        "J": "SKWR -PBLG",
        "K": "K -BG",
        "L": "HR -L",
        "M": "PH -PL",
        "N": "TPH -PB",
        "NG": "TPH -PBG",
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

        
        "D S": "STK",
        "D S T": "STK",
        "D S K": "STK",
        "K N": "K",
        "K M P": "KP",
        "K M B": "KPW",
        "L F": "-FL",
        "L V": "-FL",
        "G L": "-LG",
        "L J": "-LG",
        "K L": "*LG",
        "N J": "-PBG",
        "M J": "-PLG",
        "R F": "*FR",
        "R S": "*FR",
        "R M": "*FR",
        "R V": "-FRB",
        "L CH": "-LG",
        "R CH": "-FRPB",
        "N CH": "-FRPBLG",
        "L SH": "*RB",
        "R SH": "*RB",
        "N SH": "*RB",
        "M P": "*PL",
        "T L": "-LT",
        "S T": "*S",
        "SH N": "-GS",
        "K SH N": "-BGS",
        "NG G": "-PBG",
        "NG K": "*PBG",

        "@ N T": "SPW",
        "@ N D": "SPW",
        "@ M P": "KPW",
        "@ M B": "KPW",
        "@ N K": "SKPW",
        "@ N G": "SKPW",
        "@ N J": "SKPW",
        "E K S": "SKW",
        "E K S T": "STKW",
        "E K S K": "SKW",
        "E K S P": "SKPW",
        "@ N S": "STPH",
        "@ N F": "TPW",
        "@ N V": "TPW",

        "@": "@",
    }

    sophs_to_alternate_chords = {
        "F": "W",
        "J": "-FR",
        "K": "*G",
        "M": "-FR",
        "S": "-F",
        "TH": "-F",
        "V": "W -F",
        "Z": "S* -F",
    }

    yield soph_trie(
        map_phoneme_to_sophs=map_phoneme_to_sophs,
        sophs_to_chords_dicts=(sophs_to_main_chords, sophs_to_alternate_chords),
        vowel_sophs_str="A AA E EE I II O OO U UU AU OI OU",
    )


    yield alt_chords(
        sophs_to_alternate_chords_dicts=(sophs_to_alternate_chords,),
        sophs_to_main_chords_dicts=(sophs_to_main_chords,),
    )


    def map_phonemes_to_sophemes_by_sophs(mappings: dict[str, str]):
        def parse_sopheme(sopheme_str: str):
            return next(parse_sopheme_seq(sopheme_str))


        chords = {
            Soph(key): parse_sopheme(sopheme_str)
            for key, sopheme_str in mappings.items()
        }


        def generate(phoneme: SophemeSeqPhoneme):
            for soph in map_phoneme_to_sophs(phoneme):
                if soph not in chords: continue
                yield chords[soph]

        return generate


    yield diphthong_transition_consonants(
        keysymbols_by_first_vowel=map_phonemes_to_sophemes_by_sophs({
            "E": ".y?",
            "OO": ".w?",
            "OU": ".w?",
            "I": ".y?",
            "EE": ".y?",
            "UU": ".w?",
            "AA": ".y?",
            "OI": ".y?",
            "II": ".y?",
        }),
    )


    yield amphitheory_outlines()


    yield optional_middle_vowels()


    def if_phoneme_maps_to(soph_values: str):
        sophs = set(Soph(value) for value in soph_values.split())
        def check(phoneme: SophemeSeqPhoneme):
            return any(soph in sophs for soph in map_phoneme_to_sophs(phoneme))

        return check


    yield optional_middle_consonants(
        make_optional_if=if_phoneme_maps_to("Y W"),
    )

    yield optional_unstressed_middle_consonants(
        make_optional_if=if_phoneme_maps_to("R N L"),
    )