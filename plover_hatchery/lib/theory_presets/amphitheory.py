from collections.abc import Generator
from typing import Any, Generator

from plover_hatchery_lib_rs import DefViewCursor, DefViewItem, Keysymbol
from plover_hatchery.lib.pipes import *
from plover_hatchery.lib.sopheme.parse.parse_sopheme_sequence import parse_keysymbol_seq

@compile_theory
def theory():
    yield floating_keys("*")


    def map_phoneme_to_soph_values_base(cursor: DefViewCursor) -> Generator[str, None, None]:
        match cursor.nth(cursor.stack_len - 1):
            case DefViewItem.Sopheme(sopheme):
                keysymbol = sopheme.keysymbols[cursor.index_stack[-1]]


                if keysymbol.symbol == "s":
                    if "sc" in sopheme.chars:
                        yield "SC"
                        return
                    elif "c" in sopheme.chars:
                        yield "C"
                        return
                
                
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





                as_spelled = ""
                if any(part in sopheme.chars for part in ("aw", "au")):
                    as_spelled = "AU"
                elif any(part in sopheme.chars for part in ("ow", "ou")):
                    as_spelled = "OU"
                elif any(part in sopheme.chars for part in ("oi", "oy")):
                    as_spelled = "OI"
                elif any(part in sopheme.chars for part in ("ai", "ay")):
                    as_spelled = "AA"
                elif any(part in sopheme.chars for part in ("ew",)):
                    as_spelled = "UU"
                elif any(part in sopheme.chars for part in ("ei",)):
                    as_spelled = "E"
                elif any(part in sopheme.chars for part in ("a",)):
                    as_spelled = "A AA"
                elif any(part in sopheme.chars for part in ("e",)):
                    as_spelled = "E EE"
                elif any(part in sopheme.chars for part in ("i",)):
                    as_spelled = "I II"
                elif any(part in sopheme.chars for part in ("o",)):
                    as_spelled = "O OO"
                elif any(part in sopheme.chars for part in ("u",)):
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

                sophones = mapping.get(keysymbol.symbol, keysymbol.symbol).split()

                if any(sophone in sophones for sophone in ("O", "AU")) and "a" in sopheme.chars:
                    yield "A"
                    yield "AU"
                
                if "EE" in sophones and any(chars in sopheme.chars for chars in ("i", "y")) and "e" not in sopheme.chars:
                    yield "I"
                    return

                yield from sophones

        
            case _:
                return
    
    vowel_sophs = set(value for value in "A AA E EE I II O OO U UU AU OI OU".split())

    def map_phoneme_to_soph_values(cursor: DefViewCursor) -> Generator[str, None, None]:
        sophs = tuple(map_phoneme_to_soph_values_base(cursor))
        yield from sophs

        if any(soph in vowel_sophs for soph in sophs):
            yield "@"


    def map_keysymbol_to_sophs(cursor: DefViewCursor):
        return (Soph(value) for value in map_phoneme_to_soph_values_base(cursor))


    # def map_sopheme_to_sophs(sopheme: Sopheme):
    #     return (map_phoneme_to_sophs(phoneme) for phoneme in sopheme)


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


        "C": "KPW",
        "SC": "SKPW",
    }

    sophs_to_alternate_chords = {
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

    yield soph_trie(
        map_to_sophs=map_phoneme_to_soph_values,
        sophs_to_chords_dicts=(sophs_to_main_chords, sophs_to_alternate_chords),
    )


    yield debug_stroke("@*")
    yield conflict_cycler_stroke("@")
    yield amphitheory_outlines()


    yield alt_chords(
        sophs_to_alternate_chords_dicts=(sophs_to_alternate_chords,),
        sophs_to_main_chords_dicts=(sophs_to_main_chords,),
    )


    def map_keysymbols_to_keysymbols_by_sophs(mappings: dict[str, str]):
        chords = {
            Soph(key): parse_keysymbol_seq(keysymbols_str)
            for key, keysymbols_str in mappings.items()
        }


        def generate(cursor: DefViewCursor) -> Generator[Keysymbol, None, None]:
            for soph in map_keysymbol_to_sophs(cursor):
                if soph not in chords: continue
                yield from chords[soph]

        return generate


    yield diphthong_transition_consonants(
        keysymbols_by_first_vowel=map_keysymbols_to_keysymbols_by_sophs({
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


    def if_phoneme_maps_to(soph_values: str):
        sophs = set(Soph(value) for value in soph_values.split())
        def check(cursor: DefViewCursor):
            return any(soph in sophs for soph in map_keysymbol_to_sophs(cursor))

        return check


    yield optional_middle_consonants(
        make_optional_if=if_phoneme_maps_to("Y W"),
    )

    yield optional_unstressed_middle_consonants(
        make_optional_if=if_phoneme_maps_to("R N L"),
    )



    yield consonant_inversions(
        consonant_sophs_str="B CH D F G H J K L M N NG P R S SH T TH W V Y Z ZH  C SC",
        inversion_domains_steno="STKPWHR FRPBLGTSDZ"
    )