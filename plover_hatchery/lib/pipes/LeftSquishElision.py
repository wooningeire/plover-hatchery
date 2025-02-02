from plover.steno import Stroke

from ..trie import TransitionCostInfo, NondeterministicTrie
from ..theory_defaults.amphitheory import amphitheory


class LeftSquishElision:
    """Elide vowels by attaching a new left consonant to the previous left consonant"""

    def __init__(self):
        self.__left_elision_squish_src_nodes: tuple[int, ...] = ()

    def set_src_nodes(self, nodes: tuple[int, ...]):
        self.__left_elision_squish_src_nodes = nodes

    def execute(self, trie: NondeterministicTrie[str, str], translation: str, new_left_consonant_node: int, stroke: Stroke, additional_cost: int):
        for src_node in self.__left_elision_squish_src_nodes:
            trie.link_chain(
                src_node,
                new_left_consonant_node,
                stroke.keys(),
                TransitionCostInfo(amphitheory.spec.TransitionCosts.VOWEL_ELISION + additional_cost, translation)
            )

    def clone(self):
        clone = LeftSquishElision()
        clone.__left_elision_squish_src_nodes = self.__left_elision_squish_src_nodes
        return clone