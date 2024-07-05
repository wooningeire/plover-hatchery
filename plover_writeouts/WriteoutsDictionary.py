from typing import Optional
import json

from plover.steno import Stroke
from plover.steno_dictionary import StenoDictionary
import plover.log

from plover_writeouts.lib.DagTrie import DagTrie

def split_stroke_parts(stroke: Stroke):
    _LEFT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("STKPWHR")
    _VOWELS_SUBSTROKE = Stroke.from_steno("AOEU")
    _RIGHT_BANK_CONSONANTS_SUBSTROKE = Stroke.from_steno("-FRPBLGTSDZ")

    left_bank_consonants = stroke & _LEFT_BANK_CONSONANTS_SUBSTROKE
    vowels = stroke & _VOWELS_SUBSTROKE
    right_bank_consonants = stroke & _RIGHT_BANK_CONSONANTS_SUBSTROKE

    return left_bank_consonants, vowels, right_bank_consonants


_STROKE_BOUNDARY = "/"

class WriteoutsDictionary(StenoDictionary):
    readonly = True


    def __init__(self):
        super().__init__()

        """(override)"""
        self._longest_key = 8

        self.__dag_trie: Optional[DagTrie[str, str]] = None

    def _load(self, filepath: str):
        with open(filepath, "r") as file:
            map: dict[str, str] = json.load(file)

        dag_trie: DagTrie[str, str] = DagTrie()
        self.__dag_trie = dag_trie

        _CHORD_ALTERNATIVES: dict[Stroke, Stroke] = {
            Stroke.from_steno(steno_main): Stroke.from_steno(steno_alt)
            for steno_main, steno_alt in {
                "-F": "TP",
                "-FB": "SR",
                "-FL": "TPHR",
                "-R": "R",
                "-P": "P",
                "-PB": "TPH",
                "-PL": "PH",
                "-B": "PW",
                "-BG": "K",
                "-L": "HR",
                "-G": "TKPW",
                "-T": "T",
                "-S": "S",
                "-D": "TK",
                "-Z": "STKPW",
                
                "TP": "-F",
                "SR": "-FB",
                "TPHR": "-FL",
                "R": "-R",
                "P": "-P",
                "TPH": "-PB",
                "PH": "-PL",
                "PW": "-B",
                "K": "-BG",
                "HR": "-L",
                "TKPW": "-G",
                "T": "-T",
                "S": "-S",
                "TK": "-D",
                "STKPW": "-Z",
            }.items()
        }

        _LTR_CONSONANTS: dict[Stroke, Stroke] = {
            Stroke.from_steno(steno_main): Stroke.from_steno(steno_alt)
            for steno_main, steno_alt in {
                "TP": "-F",
                "SR": "-FB",
                "TPHR": "-FL",
                "R": "-R",
                "P": "-P",
                "TPH": "-PB",
                "PH": "-PL",
                "PW": "-B",
                "K": "-BG",
                "HR": "-L",
                "TKPW": "-G",
                "T": "-T",
                "S": "-S",
                "TK": "-D",
                "STKPW": "-Z",
            }.items()
        }

        _LTR_F_CONSONANTS: dict[Stroke, Stroke] = {
            Stroke.from_steno(steno_main): Stroke.from_steno(steno_alt)
            for steno_main, steno_alt in {
                "S": "-F",
                "PH": "-FR",
            }.items()
        }

        for outline_steno, translation in map.items():
            current_head = DagTrie.ROOT

            last_prevowels_node = None
            last_preboundary_node = None
            last_alternate_right_base_nodes: list[int] = []
            last_alternate_stroke_start_node = None
            consonants_since_last_vowel = []

            for i, stroke_steno in enumerate(outline_steno.split("/")):
                if i > 0:
                    current_head = dag_trie.get_dst_node_else_create(current_head, _STROKE_BOUNDARY)

                stroke = Stroke.from_steno(stroke_steno)

                left_bank_consonants, vowels, right_bank_consonants = split_stroke_parts(stroke)

                if len(left_bank_consonants) > 0:
                    current_head = dag_trie.get_dst_node_else_create_chain(current_head, left_bank_consonants.keys())

                    # after first consonant phoneme: elision of previous stroke's vowels
                    if last_prevowels_node is not None:
                        dag_trie.link_chain(last_prevowels_node, current_head, left_bank_consonants.keys())

                    if last_alternate_stroke_start_node is not None:
                        dag_trie.link_chain(last_alternate_stroke_start_node, current_head, left_bank_consonants.keys())


                    # after all consonant phonemes: reattachment of consonant to previous stroke
                    new_alternate_right_base_nodes: list[int] = []
                    new_alternate_stroke_start_node = None
                    if left_bank_consonants in _LTR_CONSONANTS and last_preboundary_node is not None:
                        alternate_head = dag_trie.get_dst_node_else_create_chain(last_preboundary_node, _LTR_CONSONANTS[left_bank_consonants].keys())
                        new_alternate_right_base_nodes.append(alternate_head)

                        # chain together ending chords
                        for node in last_alternate_right_base_nodes:
                            dag_trie.link_chain(node, alternate_head, _LTR_CONSONANTS[left_bank_consonants].keys())


                        alternate_head = dag_trie.get_dst_node_else_create(alternate_head, _STROKE_BOUNDARY)
                        new_alternate_stroke_start_node = alternate_head

                        dag_trie.link_chain(alternate_head, current_head, Stroke.from_steno("KWR").keys())

                    if left_bank_consonants in _LTR_F_CONSONANTS and last_preboundary_node is not None:
                        alternate_head = dag_trie.get_dst_node_else_create_chain(last_preboundary_node, _LTR_F_CONSONANTS[left_bank_consonants].keys())

                        # chain together ending chords
                        for node in last_alternate_right_base_nodes:
                            dag_trie.link_chain(node, alternate_head, _LTR_F_CONSONANTS[left_bank_consonants].keys())

                        new_alternate_right_base_nodes.append(alternate_head)
                    
                    last_alternate_right_base_nodes = new_alternate_right_base_nodes
                    last_alternate_stroke_start_node = new_alternate_stroke_start_node

                last_prevowels_node = current_head

                # can't really do anything all that special with vowels, so only proceed through a vowel transition
                # if it matches verbatim
                if len(vowels) > 0:
                    current_head = dag_trie.get_dst_node_else_create(current_head, vowels.rtfcre)

                if len(right_bank_consonants) > 0:
                    current_head = dag_trie.get_dst_node_else_create_chain(current_head, right_bank_consonants.keys())

                    # after first consonant phoneme: elision of this stroke's vowels
                    for node in last_alternate_right_base_nodes:
                        dag_trie.link_chain(node, current_head, right_bank_consonants.keys())

                last_preboundary_node = current_head




            dag_trie.set_translation(current_head, translation)


    def __getitem__(self, stroke_stenos: tuple[str, ...]) -> str:
        result = self.__lookup(stroke_stenos)
        if result is None:
            raise KeyError
        
        return result

    def get(self, stroke_stenos: tuple[str, ...], fallback=None) -> Optional[str]:
        result = self.__lookup(stroke_stenos)
        if result is None:
            return fallback
        
        return result
    
    def __lookup(self, stroke_stenos: tuple[str, ...]) -> Optional[str]:
        if self.__dag_trie is None:
            raise Exception("lookup occurred before load")

        current_head = DagTrie.ROOT

        dag_trie = self.__dag_trie

        plover.log.info("new lookup")

        for i, stroke_steno in enumerate(stroke_stenos):
            stroke = Stroke.from_steno(stroke_steno)
            if len(stroke) == 0:
                return None
            
            if i > 0:
                current_head = dag_trie.get_dst_node(current_head, _STROKE_BOUNDARY)
                if current_head is None:
                    return None

            left_bank_consonants, vowels, right_bank_consonants = split_stroke_parts(stroke)

            if len(left_bank_consonants) > 0:
                left_bank_consonants_keys = left_bank_consonants.keys()
                current_head = dag_trie.get_dst_node_chain(current_head, left_bank_consonants_keys)
                plover.log.info(left_bank_consonants_keys)

                if current_head is None:
                    return None

            if len(vowels) == 0:
                return None
            plover.log.info(vowels)
            current_head = dag_trie.get_dst_node(current_head, vowels.rtfcre)
            if current_head is None:
                return None

            if len(right_bank_consonants) > 0:
                right_bank_consonants_keys = right_bank_consonants.keys()
                current_head = dag_trie.get_dst_node_chain(current_head, right_bank_consonants_keys)
                plover.log.info(right_bank_consonants_keys)
                if current_head is None:
                    return None

        return dag_trie.get_translation(current_head)

