from collections.abc import Generator
from typing import Any, Generator

from plover_hatchery_lib_rs import DefViewCursor, DefViewItem, SoundSymbol, parse_sound_symbol_seq
from plover_hatchery.lib.pipes import *

@compile_theory
def theory():
    yield floating_keys("*")

    
    def as_spelled_in(string: str):
        if any(part in string for part in ("aw", "au")):
            return "AU"
        if any(part in string for part in ("ow", "ou")):
            return "OU"
        if any(part in string for part in ("oi", "oy")):
            return "OI"
        if any(part in string for part in ("ai", "ay")):
            return "AA"
        if any(part in string for part in ("ew",)):
            return "UU"
        if any(part in string for part in ("ei",)):
            return "E"
        if any(part in string for part in ("a",)):
            return "A AA"
        if any(part in string for part in ("e",)):
            return "E EE"
        if any(part in string for part in ("i",)):
            return "I II"
        if any(part in string for part in ("o",)):
            return "O OO"
        if any(part in string for part in ("u",)):
            return "U UU"

        return ""



    def map_phoneme_to_theory_symbol_values_base(cursor: DefViewCursor) -> Generator[str, None, None]:
        match cursor.tip():
            case DefViewItem.Sopheme(sopheme):
                if len(sopheme.keysymbols) > 0: return

                spelling = cursor.spelling_including_silent()
                yield from as_spelled_in(spelling).split()


            case DefViewItem.Keysymbol(keysymbol):
                sopheme = cursor.nth(cursor.stack_len - 1).sopheme()


                if keysymbol.value == "s":
                    if "sc" in sopheme.chars:
                        yield "SC"
                        return
                    elif "c" in sopheme.chars:
                        yield "C"
                        return
                    elif "z" in sopheme.chars:
                        yield "Z"
                
                if keysymbol.value == "z":
                    if "s" in sopheme.chars:
                        yield "S"
                
                if keysymbol.stress > 1:
                    if any(chars in sopheme.chars for chars in ("ai", "ay")):
                        yield "AA"
                    elif any(chars in sopheme.chars for chars in ("oi", "oy")):
                        yield "OI"
                    elif any(chars in sopheme.chars for chars in ("au", "aw")):
                        yield "AU"
                    elif any(chars in sopheme.chars for chars in ("ou", "ow")):
                        yield "OU"
                    elif any(chars in sopheme.chars for chars in ("a",)):
                        yield "A"
                        yield "AA"
                    elif any(chars in sopheme.chars for chars in ("o",)):
                        yield "O"
                        yield "OO"
                    elif any(chars in sopheme.chars for chars in ("e",)):
                        yield "E"
                        yield "EE"
                    elif any(chars in sopheme.chars for chars in ("u",)):
                        yield "U"
                        yield "UU"
                    elif any(chars in sopheme.chars for chars in ("i",)):
                        yield "I"
                        yield "II"



                as_spelled = as_spelled_in(sopheme.chars)

                if keysymbol.is_vowel and keysymbol.stress != 1:
                    yield from as_spelled.split(" ")

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

                sophones = mapping.get(keysymbol.value, keysymbol.value).split()

                if any(sophone in sophones for sophone in ("O", "AU")) and "a" in sopheme.chars:
                    yield "A"
                    yield "AU"
                
                if "EE" in sophones and any(chars in sopheme.chars for chars in ("i", "y")) and "e" not in sopheme.chars:
                    yield "I"
                    return

                yield from sophones

        
            case _:
                return
    
    vowel_theory_symbols = set(value for value in "A AA E EE I II O OO U UU AU OI OU".split())

    def map_phoneme_to_theory_symbol_values(cursor: DefViewCursor) -> Generator[str, None, None]:
        theory_symbols = tuple(map_phoneme_to_theory_symbol_values_base(cursor))
        yield from theory_symbols

        if any(theory_symbol in vowel_theory_symbols for theory_symbol in theory_symbols):
            yield "@"


    def map_keysymbol_to_theory_symbols(cursor: DefViewCursor):
        return (TheorySymbol(value) for value in map_phoneme_to_theory_symbol_values_base(cursor))


    # def map_sopheme_to_theory_symbols(sopheme: Sopheme):
    #     return (map_phoneme_to_theory_symbols(phoneme) for phoneme in sopheme)


    theory_symbols_to_main_chords = {
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

        
        "D S T": "STK",
        "D S K": "STK",
        "K N": "K",
        "K M P": "KP",
        "K M B": "KPW",
        "K L": "*LG",
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
        "S T": "*S",
        "SH N": "-GS",
        "K SH N": "-BGS",
        "NG G": "-PBG", # -PB/TKPW
        "NG K": "*PBG", # -PB/K

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
        "E K C": "SKW",
        "E K C T": "STKW",
        "E K C K": "SKW",
        "E K C P": "SKPW",
        "E K SC": "SKW",
        "E K SC T": "STKW",
        "E K SC K": "SKW",
        "E K SC P": "SKPW",
        "@ N S": "STPH",
        "@ N F": "TPW",
        "@ N V": "TPW",

        "@": "@",


        "C": "KPW -S",
        "SC": "SKPW -S",
    }

    theory_symbols_to_alternate_chords = {
        "F": "W",
        "J": "-FR -G",
        "K": "*G",
        "M": "-FR",
        "S": "-F",
        "TH": "-F",
        "V": "W -F",
        "Z": "S* -F",

        "C": "S -F",
        "SC": "S -F",
    }

    yield theory_symbol_trie(
        map_to_theory_symbols=lambda cursor: set(map_phoneme_to_theory_symbol_values(cursor)),
        theory_symbols_to_chords_dicts=(theory_symbols_to_main_chords, theory_symbols_to_alternate_chords),
    )


    yield debug_stroke("@*")
    yield conflict_cycler_stroke("@")
    yield amphitheory_outlines()


    yield alt_chords(
        theory_symbols_to_alternate_chords_dicts=(theory_symbols_to_alternate_chords,),
        theory_symbols_to_main_chords_dicts=(theory_symbols_to_main_chords,),
    )


    def map_keysymbols_to_keysymbols_by_theory_symbols(mappings: dict[str, str]):
        chords = {
            TheorySymbol(key): parse_sound_symbol_seq(keysymbols_str)
            for key, keysymbols_str in mappings.items()
        }

        def generate(cursor: DefViewCursor):
            new_keysymbols = set[SoundSymbol]()

            for theory_symbol in map_keysymbol_to_theory_symbols(cursor):
                if theory_symbol not in chords: continue
                new_keysymbols.update(chords[theory_symbol])

            return new_keysymbols.__iter__()

        return generate


    yield diphthong_transition_consonants(
        keysymbols_by_first_vowel=map_keysymbols_to_keysymbols_by_theory_symbols({
            "E": "y?",
            "OO": "w?",
            "OU": "w?",
            "I": "y?",
            "EE": "y?",
            "UU": "w?",
            "AA": "y?",
            "OI": "y?",
            "II": "y?",
        }),
    )


    yield optional_middle_vowels()


    def if_phoneme_maps_to(theory_symbol_values: str):
        theory_symbols = set(TheorySymbol(value) for value in theory_symbol_values.split())
        def check(cursor: DefViewCursor):
            return any(theory_symbol in theory_symbols for theory_symbol in map_keysymbol_to_theory_symbols(cursor))

        return check


    yield optional_middle_consonants(
        make_optional_if=if_phoneme_maps_to("Y W"),
    )

    yield optional_unstressed_middle_consonants(
        make_optional_if=if_phoneme_maps_to("R N L"),
    )



    yield consonant_inversions(
        consonant_theory_symbols_str="B CH D F G H J K L M N NG P R S SH T TH W V Y Z ZH  C SC",
        inversion_domains_steno="STKPWHR FRPBLGTSDZ"
    )
