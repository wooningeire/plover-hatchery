from ..pipes import *

from ..sopheme import Sound


Sophone = define_sophones("""
S T K P W H R
Z J V D G F N Y B M L
CH SH TH
NG
A E I O U
AA EE II OO UU
AU OU OI
ANY_VOWEL
""")

vowel_sophones = {
    Sophone.AA,
    Sophone.A,
    Sophone.EE,
    Sophone.E,
    Sophone.II,
    Sophone.I,
    Sophone.OO,
    Sophone.O,
    Sophone.UU,
    Sophone.U,
    Sophone.AU,
    Sophone.OI,
    Sophone.OU,
}


def default_sound_to_sophone_mapping(sound: Sound):
    spelled = {
        "a": "A",
        "e": "E",
        "i": "I",
        "o": "O",
        "u": "U",
    }.get(sound.sopheme.chars)

    return Sophone.__dict__[{
        "p": ("P",),
        "t": ("T", "D"),
        "?": (),  # glottal stop
        "t^": ("T", "R"),  # tapped R
        "k": ("K",),
        "x": ("K",),
        "b": ("B",),
        "d": ("D", "T"),
        "g": ("G",),
        "ch": ("CH",),
        "jh": ("J",),
        "s": ("S",),
        "z": ("Z",),
        "sh": ("SH",),
        "zh": ("SH", "J"),
        "f": ("F",),
        "v": ("V",),
        "th": ("TH",),
        "dh": ("TH",),
        "h": ("H",),
        "m": ("M",),
        "m!": ("M",),
        "n": ("N",),
        "n!": ("N",),
        "ng": ("NG",),
        "l": ("L",),
        "ll": ("L",),
        "lw": ("L",),
        "l!": ("L",),
        "r": ("R",),
        "y": ("Y",),
        "w": ("W",),
        "hw": ("W",),
        
        "e": ("E", "EE", "AA"),
        "ao": ("A", "AA", "O", "U"),
        "a": ("A", "AA"),
        "ah": ("A", "O"),
        "oa": ("A", "O", "U"),
        "aa": ("O", "A"),
        "ar": ("A",),
        "eh": ("A",),
        "ou": ("OO", "O"),
        "ouw": ("OO",),
        "oou": ("OO",),
        "o": ("O",),
        "au": ("O", "A"),
        "oo": ("O",),
        "or": ("O",),
        "our": ("O",),
        "ii": ("EE",),
        "iy": ("EE",),
        "i": ("I", "EE", "E"),
        "@r": (spelled,),
        "@": (spelled,),
        "uh": ("U",),
        "u": ("U", "O", "OO"),
        "uu": ("UU",),
        "iu": ("UU",),
        "ei": ("AA", "E"),
        "ee": ("AA", "E", "A"),
        "ai": ("II",),
        "ae": ("II",),
        "aer": ("II",),
        "aai": ("II",),
        "oi": ("OI",),
        "oir": ("OI",),
        "ow": ("OU",),
        "owr": ("OU",),
        "oow": ("OU",),
        "ir": ("EE",),
        "@@r": (spelled,),
        "er": ("E", "U"),
        "eir": ("E",),
        "ur": ("U", "UU"),
        "i@": (spelled,),
    }[sound.keysymbol.base_symbol][0]]


map_sophones = sophone_mapper(Sophone, default_sound_to_sophone_mapping)


theory = compile_theory(
    declare_banks(
        left="STKPWHR",
        mid="AOEU",
        right="-FRPBLGTSDZ",
        positionless="*",
    ),

    consonants_vowels_enumeration(),

    banks(
        left_chords=map_sophones({
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

        mid_chords=map_sophones({
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
        }),

        right_chords=map_sophones({
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

    linker_chord("KWR"),

    left_squish_elision(),
    right_squish_elision(),
    boundary_elision(),

    left_alt_chords(
        chords=map_sophones({
            "V": "W",
            "Z": "S*",
        })
    ),
    left_alt_squish_elision(),

    right_alt_chords(
        chords=map_sophones({
            "S": "-F",
            "Z": "-F",
            "V": "-F",
            "K": "*G",
        })
    ),
    right_alt_squish_elision(),

    splitter_lookup(),

    path_traversal_reverse_lookup(),
    
    # consonant_clusters(
    #     Sophone,
    #     default_sound_to_sophone_mapping,
    #     {
    #         "D S": "STK",
    #         "D S T": "STK",
    #         "D S K": "STK",
    #         "K N": "K",
    #         "K M P": "KP",
    #         "K M B": "KPW",
    #         "L F": "-FL",
    #         "L V": "-FL",
    #         "G L": "-LG",
    #         "L J": "-LG",
    #         "K L": "*LG",
    #         "N J": "-PBG",
    #         "M J": "-PLG",
    #         "R F": "*FR",
    #         "R S": "*FR",
    #         "R M": "*FR",
    #         "R V": "-FRB",
    #         "L CH": "-LG",
    #         "R CH": "-FRPB",
    #         "N CH": "-FRPBLG",
    #         "L SH": "*RB",
    #         "R SH": "*RB",
    #         "N SH": "*RB",
    #         "M P": "*PL",
    #         "T L": "-LT",
    #         "S T": "*S",
    #         "SH N": "-GS",
    #         "K SH N": "-BGS",
    #     },
    #     base_cost=2,
    # ),

    # vowel_clusters(
    #     Sophone,
    #     default_sound_to_sophone_mapping,
    #     vowel_sophones,
    #     {
    #         ". N T": "SPW",
    #         ". N D": "SPW",
    #         ". M P": "KPW",
    #         ". M B": "KPW",
    #         ". N K": "SKPW",
    #         ". N G": "SKPW",
    #         ". N J": "SKPW",
    #         "E K S": "SKW",
    #         "E K S T": "STKW",
    #         "E K S K": "SKW",
    #         "E K S P": "SKPW",
    #         ". N S": "STPH",
    #         ". N F": "TPW",
    #         ". N V": "TPW",
    #     },
    #     base_cost=2,
    # ),

)