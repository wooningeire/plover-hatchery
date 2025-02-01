import plover.log

from ....util.Trie import TransitionCostInfo
from ....theory.theory import amphitheory

from ..state import EntryBuilderState
from .elision import allow_elide_previous_vowel_using_first_left_consonant

def add_left_consonant(state: EntryBuilderState):
    if len(state.left_consonant_src_nodes) == 0:
        raise Exception


    left_stroke = next(amphitheory.left_consonant_strokes(state.consonant))
    left_stroke_keys = left_stroke.keys()

    left_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.left_consonant_src_nodes[0], left_stroke_keys, TransitionCostInfo(0, state.translation))
    if len(state.left_elision_boundary_src_nodes) > 0:
        state.trie.link_chain(state.left_elision_boundary_src_nodes[0], left_consonant_node, left_stroke_keys, TransitionCostInfo(0, state.translation))

    if len(state.last_left_alt_consonant_nodes) > 0:
        state.trie.link_chain(
            state.last_left_alt_consonant_nodes[0], left_consonant_node, left_stroke_keys,
            TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT + (amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
        )

    if state.can_elide_prev_vowel_left:
        allow_elide_previous_vowel_using_first_left_consonant(state, left_stroke, left_consonant_node)
        
    left_alt_consonant_node = _add_left_alt_consonant(state, left_consonant_node)

    return left_consonant_node, left_alt_consonant_node

def _add_left_alt_consonant(state: EntryBuilderState, left_consonant_node: int):
    phoneme = amphitheory.sound_sophone(state.consonant)
    if len(state.left_consonant_src_nodes) == 0 or phoneme not in amphitheory.spec.PHONEMES_TO_CHORDS_LEFT_ALT:
        return None
    
    left_alt_stroke = amphitheory.spec.PHONEMES_TO_CHORDS_LEFT_ALT[phoneme]
    left_stroke = next(amphitheory.left_consonant_strokes(state.consonant))




    should_use_alt_from_prev = (
        state.last_consonant is None
        or state.last_consonant.keysymbol in amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT and (
            amphitheory.can_add_stroke_on(amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[amphitheory.sound_sophone(state.last_consonant)], left_stroke)
            or not amphitheory.can_add_stroke_on(amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[amphitheory.sound_sophone(state.last_consonant)], left_alt_stroke)
        )
    )
    should_use_alt_from_next = (
        state.next_consonant is None
        or state.next_consonant.keysymbol in amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT and (
            amphitheory.can_add_stroke_on(left_stroke, amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[amphitheory.sound_sophone(state.next_consonant)])
            or not amphitheory.can_add_stroke_on(left_alt_stroke, amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[amphitheory.sound_sophone(state.next_consonant)])
        )
    )
    if should_use_alt_from_prev and should_use_alt_from_next:
        return None


    left_alt_stroke_keys = left_alt_stroke.keys()

    left_alt_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.left_consonant_src_nodes[0], left_alt_stroke_keys, TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT, state.translation))
    if len(state.left_elision_boundary_src_nodes) > 0:
        state.trie.link_chain(state.left_elision_boundary_src_nodes[0], left_alt_consonant_node, left_alt_stroke_keys, TransitionCostInfo(0, state.translation))

    if len(state.last_left_alt_consonant_nodes) > 0:
        state.trie.link_chain(
            state.last_left_alt_consonant_nodes[0], left_alt_consonant_node, left_alt_stroke_keys,
            TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT + (amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
        )

    if state.can_elide_prev_vowel_left:
        # uses original left consonant node because it is ok to continue onto the vowel if the previous consonant is present
        allow_elide_previous_vowel_using_first_left_consonant(state, left_alt_stroke, left_consonant_node, amphitheory.spec.TransitionCosts.ALT_CONSONANT, False)
        allow_elide_previous_vowel_using_first_left_consonant(state, left_alt_stroke, left_alt_consonant_node, amphitheory.spec.TransitionCosts.ALT_CONSONANT)

    return left_alt_consonant_node