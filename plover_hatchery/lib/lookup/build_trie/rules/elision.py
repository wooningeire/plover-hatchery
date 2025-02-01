from plover.steno import Stroke

from ....util.Trie import TransitionCostInfo
from ....theory_defaults.amphitheory import amphitheory
from ..state import EntryBuilderState

def allow_elide_previous_vowel_using_first_left_consonant(state: EntryBuilderState, phoneme_substroke: Stroke, left_consonant_node: int, additional_cost=0, allow_boundary_elision=True):
    # Elide a vowel by attaching a new left consonant to the previous left consonant
    if len(state.left_elision_squish_src_nodes) > 0:
        state.trie.link_chain(state.left_elision_squish_src_nodes[0], left_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(amphitheory.spec.TransitionCosts.VOWEL_ELISION + additional_cost, state.translation))

    # Elide a vowel by placing the left consonant after a right consonant
    if len(state.left_elision_boundary_src_nodes) > 0 and allow_boundary_elision:
        state.trie.link_chain(state.left_elision_boundary_src_nodes[0], left_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(amphitheory.spec.TransitionCosts.VOWEL_ELISION + additional_cost, state.translation))

def allow_elide_previous_vowel_using_first_right_consonant(state: EntryBuilderState, phoneme_substroke: Stroke, right_consonant_node: int, additional_cost=0):
    if len(state.right_elision_squish_src_nodes) > 0:
        state.trie.link_chain(state.right_elision_squish_src_nodes[0], right_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(amphitheory.spec.TransitionCosts.VOWEL_ELISION + additional_cost, state.translation))

