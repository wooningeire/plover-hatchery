from plover.steno import Stroke

from ...trie import TransitionCostInfo
from ...theory_defaults.amphitheory import amphitheory
from ..state import EntryBuilderState

def allow_elide_previous_vowel_using_first_right_consonant(state: EntryBuilderState, phoneme_substroke: Stroke, right_consonant_node: int, additional_cost=0):
    if len(state.right_elision_squish_src_nodes) > 0:
        state.trie.link_chain(state.right_elision_squish_src_nodes[0], right_consonant_node, phoneme_substroke.keys(), TransitionCostInfo(amphitheory.spec.TransitionCosts.VOWEL_ELISION + additional_cost, state.translation))

