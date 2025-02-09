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


map_sophones_to_strokes = sophone_to_strokes_mapper(Sophone, default_sound_to_sophone_mapping)
map_sophones_to_sophemes = sophone_to_sopheme_mapper(Sophone, default_sound_to_sophone_mapping)


theory = compile_theory(
    declare_banks(
        left="@^STKPWHR",
        mid="AOEU",
        right="-FRPBLGTSDZ",
        positionless="*",
    ),

    consonants_vowels_enumeration(
        vowel_diphthong_transition=map_sophones_to_sophemes({
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

    banks(
        left_chords=map_sophones_to_strokes({
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

        mid_chords=map_sophones_to_strokes({
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

        right_chords=map_sophones_to_strokes({
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

    left_squish_elision(),
    right_squish_elision(),
    boundary_elision(),

    left_alt_chords(
        chords=map_sophones_to_strokes({
            "F": "W",
            "V": "W",
            "Z": "S*",
        })
    ),
    left_alt_squish_elision(),

    right_alt_chords(
        chords=map_sophones_to_strokes({
            "S": "-F",
            "Z": "-F",
            "V": "-F",
            "TH": "-F",
            "M": "-FR",
            "J": "-FR",
            "K": "*G",
        })
    ),
    right_alt_squish_elision(),
    
    consonant_clusters(
        Sophone,
        default_sound_to_sophone_mapping,
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
        Sophone,
        default_sound_to_sophone_mapping,
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

    splitter_lookup(
        cycler="@",
        prohibit_strokes=(
            "AEU",
        ),
    ),

    path_traversal_reverse_lookup(),

    # consonant_inversions(),
)


# # _keys = use_keys("@STKPWHRAO*EUFRPBLGTSDZ")
# # _key_banks = use_key_banks(_keys)(
# #     left="@STKPWHR"
# #     mid="AOEU"
# #     right="-FRPBLGTSDZ"
# #     positionless="*"
# # )


# # cost = use_transition_costs()


# @TheoryService.theory
# class amphitheory(TheorySpec, ABC):
#     ALL_KEYS = Stroke.from_steno("@^STKPWHRAO*EUFRPBLGTSDZ")


#     LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("@^STKPWHR")
#     VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
#     RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")
#     ASTERISK_SUBSTROKE = Stroke.from_steno("*")


#     PHONEMES_TO_CHORDS_VOWELS: dict[Sophone, Stroke] = {
#         phoneme: Stroke.from_steno(steno)
#         for phoneme, steno in {
#             Sophone.AA: "AEU",
#             Sophone.A: "A",
#             Sophone.EE: "AOE",
#             Sophone.E: "E",
#             Sophone.II: "AOEU",
#             Sophone.I: "EU",
#             Sophone.OO: "OE",
#             Sophone.O: "O",
#             Sophone.UU: "AOU",
#             Sophone.U: "U",
#             Sophone.AU: "AU",
#             Sophone.OI: "OEU",
#             Sophone.OU: "OU",
#             Sophone.AE: "AE",
#             Sophone.AO: "AO",
#         }.items()
#     }

#     PHONEMES_TO_CHORDS_RIGHT: dict[Sophone, Stroke] = {
#         phoneme: Stroke.from_steno(steno)
#         for phoneme, steno in {
#             Sophone.DUMMY: "",

#             Sophone.F: "-F",
#             Sophone.R: "-R",
#             Sophone.P: "-P",
#             Sophone.B: "-B",
#             Sophone.L: "-L",
#             Sophone.G: "-G",
#             Sophone.T: "-T",
#             Sophone.S: "-S",
#             Sophone.D: "-D",
#             Sophone.Z: "-Z",

#             Sophone.V: "-FB",
#             Sophone.N: "-PB",
#             Sophone.M: "-PL",
#             Sophone.K: "-BG",
#             Sophone.J: "-PBLG",
#             Sophone.CH: "-FP",
#             Sophone.SH: "-RB",
#             Sophone.TH: "*T",
#         }.items()

#         # "SHR": "shr",
#         # "THR": "thr",
#         # "KHR": "chr",
#         # "-FRP": (Phoneme.M, Phoneme.P),
#         # "-FRB": (Phoneme.R, Phoneme.V),
#     }

#     PHONEMES_TO_CHORDS_RIGHT_ALT: dict[Sophone, Stroke] = {
#         phoneme: Stroke.from_steno(steno)
#         for phoneme, steno in {
#             Sophone.S: "-F",
#             Sophone.Z: "-F",
#             Sophone.V: "-F",
#             Sophone.TH: "-F",
#             Sophone.M: "-FR",
#             Sophone.J: "-FR",
#             Sophone.K: "*G",
#         }.items()
#     }

#     LINKER_CHORD = Stroke.from_steno("SWH")
#     INITIAL_VOWEL_CHORD = Stroke.from_steno("@")

#     CYCLER_STROKE = Stroke.from_steno("@")
#     # CYCLER_STROKE_BACKWARD = Stroke.from_steno("+*")

#     PROHIBITED_STROKES = {
#         Stroke.from_steno(steno)
#         for steno in ("AEU",)
#     }

#     DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL: dict[Sophone, Sophone] = {
#         prev_vowel_phoneme: phoneme
#         for prev_vowel_phoneme, phoneme in {
#             Sophone.E: Sophone.Y,
#             Sophone.OO: Sophone.W,
#             Sophone.OU: Sophone.W,
#             Sophone.I: Sophone.Y,
#             Sophone.EE: Sophone.Y,
#             Sophone.UU: Sophone.W,
#             Sophone.AA: Sophone.Y,
#             Sophone.OI: Sophone.Y,
#             Sophone.II: Sophone.Y,
#         }.items()
#     }

#     class TransitionCosts(TheorySpec.TransitionCosts, ABC):
#         VOWEL_ELISION = 5
#         CLUSTER = 2
#         ALT_CONSONANT = 3
