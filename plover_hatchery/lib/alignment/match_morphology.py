
from abc import ABC
import dataclasses
from typing import NamedTuple
from plover_hatchery.lib.alignment.alignment import AlignmentService, Cell, aligner
from plover_hatchery.lib.alignment.parse_morphology import Affix, Formatting, FreeMorpheme, MorphologyPart


_VOWELS = "aeiou"

_AFFIX_MAPPINGS = {
    name: tuple(options.split())
    for name, options in {
        "ise": "ise ize"
    }.items()
}

class _Cost(NamedTuple):
    n_unmatched_parts: int
    n_unmatched_chars: int
    n_chunks: int

@aligner
class match_morphology_to_chars(AlignmentService, ABC):
    @staticmethod
    def initial_cost():
        return _Cost(0, 0, 0)
    
    @staticmethod
    def mismatch_cost(mismatch_parent: Cell[_Cost, None], increment_x: bool, increment_y: bool):
        return _Cost(
            mismatch_parent.cost.n_unmatched_parts + (1 if increment_x else 0),
            mismatch_parent.cost.n_unmatched_chars + (1 if increment_y else 0),
            mismatch_parent.cost.n_chunks + 1 if mismatch_parent.has_match else mismatch_parent.cost.n_chunks,
        )

    @staticmethod
    def has_mapping(candidate_x_key: tuple[MorphologyPart, ...]) -> bool:
        return len(candidate_x_key) == 1

    @staticmethod
    def get_mapping_options(candidate_x_key: tuple[MorphologyPart, ...]):
        part = candidate_x_key[0]

        if isinstance(part, FreeMorpheme):
            yield "".join(bound.name for bound in part.parts)
            return

        if isinstance(part, Formatting):
            yield part.name
            return

        
        # Elide vowels at the end of the affix

        if part.name in _AFFIX_MAPPINGS:
            affix_options = _AFFIX_MAPPINGS[part.name]
        else:
            affix_options = (part.name,)
        
        for option in affix_options:
            for start in range(0, len(part.name)):
                if start > 0 and option[start - 1] not in _VOWELS:
                    break

                for end in range(len(part.name) - 1, start - 1, -1):
                    if end < len(part.name) - 1 and option[end + 1] not in _VOWELS:
                        break

                    yield option[start:end + 1]

    @staticmethod
    def is_match(actual_chars: str, candidate_chars: str):
        return actual_chars == candidate_chars
    
    @staticmethod
    def match_cost(parent: Cell[_Cost, None]):
        return _Cost(
            parent.cost.n_unmatched_parts,
            parent.cost.n_unmatched_chars,
            parent.cost.n_chunks + 1,
        )
    
    @staticmethod
    def match_data(subseq_parts: tuple[MorphologyPart, ...], subseq_chars: str, pre_subseq_keysymbols: tuple[str, ...], pre_subseq_chars: str):
        return None

    @staticmethod
    def construct_match(parts: tuple[MorphologyPart, ...], translation: str, start_cell: Cell[_Cost, None], end_cell: Cell[_Cost, None], _: None):
        match_parts = parts[start_cell.x:end_cell.x]
        match_chars =  translation[start_cell.y:end_cell.y]

        if len(match_parts) == 0:
            return Formatting(match_chars, match_chars)
        
        return dataclasses.replace(match_parts[0], ortho=match_chars)