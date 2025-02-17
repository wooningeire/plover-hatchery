import itertools

from ..pipes import *

from ..sopheme import Sound


def as_spelled(sound: Sound):
    return {
        "a": "A",
        "e": "E",
        "i": "I",
        "o": "O",
        "u": "U",
    }.get(sound.sopheme.chars, "")

sophone_type = SophoneType.create_with_sophones("""
S T K P W H R
Z J V D G F N Y B M L
CH SH TH
NG
A E I O U
AA EE II OO UU
AU OU OI
""", {
    "p": "P",
    "t": "T D",
    "?": "",  # glottal stop
    "t^": "T R",  # tapped R
    "k": "K",
    "x": "K",
    "b": "B",
    "d": "D T",
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
    
    "e": "E EE AA",
    "ao": "A AA O U",
    "a": "A AA",
    "ah": "A O",
    "oa": "A O U",
    "aa": "O A",
    "ar": "A",
    "eh": "A",
    "ou": "OO O",
    "ouw": "OO",
    "oou": "OO",
    "o": "O",
    "au": "O A",
    "oo": "O",
    "or": "O",
    "our": "O",
    "ii": "EE",
    "iy": "EE",
    "i": "I EE E",
    "@r": as_spelled,
    "@": as_spelled,
    "uh": "U",
    "u": "U O OO",
    "uu": "UU",
    "iu": "UU",
    "ei": "AA E",
    "ee": "AA E A",
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
    "er": "E U",
    "eir": "E",
    "ur": "U UU",
    "i@": as_spelled,
})

vowel_sophones = set(sophone_type.iterate("""
A E I O U
AA EE II OO UU
AU OI OU
"""))



theory = compile_theory(
    declare_banks(
        left="@^STKPWHR",
        mid="AOEU",
        right="-FRPBLGTSDZ",
        positionless="*",
    ),

    consonants_vowels_enumeration(
        vowel_diphthong_transition=sophone_type.mapper_to_sophemes({
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
    ),

    key_by_key_lookup(
        cycle_on="@",
        debug_on="@*",
        prohibit_strokes=(
            "AEU",
        ),
    ),

    path_traversal_reverse_lookup(),

    banks(
        left_chords=sophone_type.mapper_to_chords({
            "S": "S",
            "T": "T",
            "K": "K",
            "P": "P",
            "W": "W",
            "H": "H",
            "R": "R",

            "Z": "STKPW",
            "J": "SKWR",
            "V": "SR",
            "D": "TK",
            "G": "TKPW",
            "F": "TP",
            "N": "TPH",
            "Y": "KWR",
            "B": "PW",
            "M": "PH",
            "L": "HR",

            "SH": "SH",
            "TH": "TH",
            "CH": "KH",

            "NG": "TPH",
        }),

        mid_chords=lambda sound: itertools.chain(
            map_unstressed_vowels({
                "a": ("A", "AEU"),
                "e": ("E", "AOE"),
                "i": ("EU", "AOEU"),
                "o": ("O", "OE"),
                "u": ("U", "AOU"),
            })(sound),
            sophone_type.mapper_to_chords({
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
            })(sound),
        ),

        right_chords=sophone_type.mapper_to_chords({
            "F": "-F",
            "R": "-R",
            "P": "-P",
            "B": "-B",
            "L": "-L",
            "G": "-G",
            "T": "-T",
            "S": "-S",
            "D": "-D",
            "Z": "-Z",

            "V": "-FB",
            "N": "-PB",
            "M": "-PL",
            "K": "-BG",
            "J": "-PBLG",
            "CH": "-FP",
            "SH": "-RB",
            "TH": "*T",
        }),
    ),

    linker_chord("^"),

    initial_vowel_chord("@"),

    optional_middle_vowels(),
    optional_middle_consonants(
        ignore_consonant_if=sophone_type.given_sound_maps_to_sophones("Y W"),
    ),
    optional_unstressed_middle_consonants(
        ignore_consonant_if=sophone_type.given_sound_maps_to_sophones("R N L"),
    ),

    alternate_chords(
        left_chords=sophone_type.mapper_to_chords({
            "F": "W",
            "V": "W",
            "Z": "S*",
        }),
        
        right_chords=sophone_type.mapper_to_chords({
            "S": "-F",
            "Z": "-F",
            "V": "-F",
            "TH": "-F",
            "M": "-FR",
            "J": "-FR",
            "K": "*G",
        }),
    ),
    
    consonant_clusters(
        sophone_type,
        {
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
        },
        base_cost=2,
    ),

    vowel_clusters(
        sophone_type,
        vowel_sophones,
        {
            ". N T": "SPW",
            ". N D": "SPW",
            ". M P": "KPW",
            ". M B": "KPW",
            ". N K": "SKPW",
            ". N G": "SKPW",
            ". N J": "SKPW",
            "E K S": "SKW",
            "E K S T": "STKW",
            "E K S K": "SKW",
            "E K S P": "SKPW",
            ". N S": "STPH",
            ". N F": "TPW",
            ". N V": "TPW",
        },
        base_cost=2,
    ),

    # consonant_inversions(),
)
