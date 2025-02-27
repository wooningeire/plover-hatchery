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
CH SH ZH TH
NG
A E I O U
AA EE II OO UU
AU OU OI
""", {
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
    "ei": "AA",
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
    "eir": "E",
    "ur": "U",
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
        left_chords=take_first_match(
            yield_if(
                all_true(
                    sophone_type.given_sound_is_pronounced_as("S"),
                    given_sound_has_in_spelling_including_silent("sc"),
                ),
                chords("SKPW"),
            ),

            yield_if(
                all_true(
                    sophone_type.given_sound_is_pronounced_as("S"),
                    given_sound_has_in_spelling_including_silent("c"),
                ),
                chords("KPW"),
            ),

            sophone_type.map_given_sound_to_chords_by_sophone({
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
                "ZH": "STKPWH",

                "NG": "TPH",
            }),
        ),

        mid_chords=take_first_match(
            yield_if(
                all_true(
                    not_true(given_sound_has_stress(1)),
                    given_sound_has_in_spelling_including_silent("oi oy"),
                ),
                chords("OEU"),
            ),

            yield_if(
                all_true(
                    not_true(given_sound_has_stress(1)),
                    given_sound_has_in_spelling_including_silent("au"),
                ),
                chords("AU"),
            ),

            yield_if(
                all_true(
                    not_true(given_sound_has_stress(1)),
                    given_sound_has_in_spelling_including_silent("ou"),
                ),
                chords("OU"),
            ),

            yield_if(
                all_true(
                    not_true(given_sound_has_stress(1)),
                    given_sound_has_in_spelling_including_silent("a"),
                ),
                chords("A AEU"),
            ),

            yield_if(
                all_true(
                    not_true(given_sound_has_stress(1)),
                    given_sound_has_in_spelling_including_silent("e"),
                ),
                chords("E AOE"),
            ),

            yield_if(
                all_true(
                    not_true(given_sound_has_stress(1)),
                    given_sound_has_in_spelling_including_silent("i"),
                ),
                chords("EU AOEU"),
            ),

            yield_if(
                all_true(
                    not_true(given_sound_has_stress(1)),
                    given_sound_has_in_spelling_including_silent("o"),
                ),
                chords("O OE"),
            ),

            yield_if(
                all_true(
                    not_true(given_sound_has_stress(1)),
                    given_sound_has_in_spelling_including_silent("u"),
                ),
                chords("U AOU"),
            ),

            yield_if(
                all_true(
                    sophone_type.given_sound_is_pronounced_as("EE"),
                    given_sound_has_in_spelling_including_silent("i y"),
                    not_true(given_sound_has_in_spelling_including_silent("e")),
                ),
                chords("EU"),
            ),

            yield_if(
                all_true(
                    sophone_type.given_sound_is_pronounced_as("O AU"),
                    given_sound_has_in_spelling_including_silent("a"),
                    not_true(given_sound_has_in_spelling_including_silent("o")),
                ),
                chords("A AU"),
            ),

            sophone_type.map_given_sound_to_chords_by_sophone({
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
        ),

        right_chords=sophone_type.map_given_sound_to_chords_by_sophone({
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
            "ZH": "*RB",
            "TH": "*T",
            "NG": "-PBG -PB",
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
        left_chords=sophone_type.map_given_sound_to_chords_by_sophone({
            "F": "W",
            "V": "W",
            "Z": "S*",
        }),
        
        right_chords=sophone_type.map_given_sound_to_chords_by_sophone({
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
