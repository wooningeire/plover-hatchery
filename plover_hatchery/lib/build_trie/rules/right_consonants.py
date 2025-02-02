from typing import Optional

import plover.log

from ...trie import TransitionCostInfo
from ...config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY
from ...theory_defaults.amphitheory import amphitheory
from ...sophone.Sophone import Sophone

from ..state import EntryBuilderState


def add_right_consonant(state: EntryBuilderState, left_consonant_node: Optional[int]):
    phoneme = amphitheory.sound_sophone(state.consonant)
    if len(state.right_consonant_src_nodes) == 0 or phoneme not in amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT:
        return None, None, None
    

    right_stroke = amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[phoneme]
    right_stroke_keys = right_stroke.keys()
    
    right_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.right_consonant_src_nodes[0], right_stroke_keys, TransitionCostInfo(0, state.translation))


    if len(state.last_right_alt_consonant_nodes) > 0:
        state.trie.link_chain(state.last_right_alt_consonant_nodes[0], right_consonant_node, right_stroke_keys, TransitionCostInfo(amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0, state.translation))

    last_phoneme = amphitheory.sound_sophone(state.last_consonant) if state.last_consonant is not None else None
    # Skeletals and right-bank consonant addons
    can_use_main_prev = (
        state.last_consonant is None
        or last_phoneme in amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT and amphitheory.can_add_stroke_on(amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[last_phoneme], right_stroke)
    )
    if len(state.prev_left_consonant_nodes) > 0 and not can_use_main_prev:
        state.trie.link_chain(state.prev_left_consonant_nodes[0], right_consonant_node, right_stroke_keys, TransitionCostInfo(0, state.translation))


    pre_rtl_stroke_boundary_node = state.right_squish_elision.get_src_nodes()[0] if len(state.right_squish_elision.get_src_nodes()) > 0 else None
    rtl_stroke_boundary_node = None

    if left_consonant_node is not None and phoneme is not Sophone.DUMMY:
        pre_rtl_stroke_boundary_node = right_consonant_node
        rtl_stroke_boundary_node = state.trie.get_first_dst_node_else_create(right_consonant_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))
        state.trie.link(rtl_stroke_boundary_node, left_consonant_node, TRIE_LINKER_KEY, TransitionCostInfo(0, state.translation))
        

    if state.is_first_consonant:
        state.right_squish_elision.execute(state.trie, state.translation, right_consonant_node, right_stroke, 0)


    right_consonant_f_node = _add_right_alt_consonant(state, right_consonant_node)

    rtl_stroke_boundary_adjacent_nodes = None
    if rtl_stroke_boundary_node is not None:
        rtl_stroke_boundary_adjacent_nodes = (pre_rtl_stroke_boundary_node, rtl_stroke_boundary_node)
    return right_consonant_node, right_consonant_f_node, rtl_stroke_boundary_adjacent_nodes

def _add_right_alt_consonant(state: EntryBuilderState, right_consonant_node: int):
    phoneme = amphitheory.sound_sophone(state.consonant)
    if len(state.right_consonant_src_nodes) == 0 or phoneme not in amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT_ALT:
        return None
    
    right_alt_stroke = amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT_ALT[phoneme]
    right_stroke = amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[phoneme]

    last_phoneme = amphitheory.sound_sophone(state.last_consonant) if state.last_consonant is not None else None
    should_use_alt_from_prev = (
        state.last_consonant is None
        or last_phoneme in amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT and (
            amphitheory.can_add_stroke_on(amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[last_phoneme], right_stroke)
            or not amphitheory.can_add_stroke_on(amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[last_phoneme], right_alt_stroke)
        )
    )
    next_phoneme = amphitheory.sound_sophone(state.next_consonant) if state.next_consonant is not None else None
    should_use_alt_from_next = (
        state.next_consonant is None
        or next_phoneme in amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT and (
            amphitheory.can_add_stroke_on(right_stroke, amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[next_phoneme])
            or not amphitheory.can_add_stroke_on(right_alt_stroke, amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[next_phoneme])
        )
    )
    if should_use_alt_from_prev and should_use_alt_from_next:
        return None


    right_alt_stroke_keys = right_alt_stroke.keys()


    right_alt_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.right_consonant_src_nodes[0], right_alt_stroke_keys, TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT, state.translation))
    if len(state.last_right_alt_consonant_nodes) > 0:
        state.trie.link_chain(
            state.last_right_alt_consonant_nodes[0], right_alt_consonant_node, right_alt_stroke_keys,
            TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT + (amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
        )

    if len(state.prev_left_consonant_nodes) > 0 and not should_use_alt_from_prev:
        state.trie.link_chain(state.prev_left_consonant_nodes[0], right_alt_consonant_node, right_alt_stroke_keys, TransitionCostInfo(0, state.translation))
        
    if state.is_first_consonant:
        state.right_squish_elision.execute(state.trie, state.translation, right_consonant_node, right_alt_stroke, amphitheory.spec.TransitionCosts.ALT_CONSONANT)

    return right_alt_consonant_node