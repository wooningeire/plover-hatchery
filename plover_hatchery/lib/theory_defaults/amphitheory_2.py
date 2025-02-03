from ..pipes import *

enumerator = SoundsEnumerator()

manage_state = use_manage_state(enumerator)


left_chords = use_left_chords(manage_state, {
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
})

use_left_alt_chords(manage_state, left_chords, {
    "F": "W",
    "V": "W",
    "Z": "S*",
})


use_consonant_clusters(manage_state, left_chords, {
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
})
use_vowel_clusters(manage_state, left_chords, {
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
    ". N": "TPH",
    ". N S": "STPH",
    ". N F": "TPW",
    ". N V": "TPW",
    ". M": "PH",
})


use_initial_vowel_chord(manage_state, "@")


# _keys = use_keys("@STKPWHRAO*EUFRPBLGTSDZ")
# _key_banks = use_key_banks(_keys)(
#     left="@STKPWHR"
#     mid="AOEU"
#     right="-FRPBLGTSDZ"
#     positionless="*"
# )

# _sophones = use_sophones("""
# S T K P W H R
# Z J V D G F N Y B M L
# CH SH TH
# NG
# A E I O U
# AA EE II OO UU
# AU OU OI
# """)



# cost = use_transition_costs()

# _left_chords = use_sophones.map.left_chords(
#     S = "S",
#     T = "T",
#     K = "K",
#     P = "P",
#     W = "W",
#     H = "H",
#     R = "R",

#     Z = "STKPW",
#     J = "SKWR",
#     V = "SR",
#     D = "TK",
#     G = "TKPW",
#     F = "TP",
#     N = "TPH",
#     Y = "KWR",
#     B = "PW",
#     M = "PH",
#     L = "HR",

#     SH = "SH",
#     TH = "TH",
#     CH = "KH",

#     NG = "TPH",
# )

# use_sophones