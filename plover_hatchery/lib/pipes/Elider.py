from plover.steno import Stroke

from ..trie import TransitionCostInfo, NondeterministicTrie
from ..theory_defaults.amphitheory import amphitheory

class Elider:
    def __init__(self):
        self.__src_nodes: tuple[int, ...] = ()

    def set_src_nodes(self, nodes: tuple[int, ...]):
        self.__src_nodes = nodes

    def get_src_nodes(self):
        return self.__src_nodes

    def execute(self, trie: NondeterministicTrie[str, str], translation: str, dst_node: int, stroke: Stroke, additional_cost: int):
        for src_node in self.__src_nodes:
            trie.link_chain(
                src_node,
                dst_node,
                stroke.keys(),
                TransitionCostInfo(amphitheory.spec.TransitionCosts.VOWEL_ELISION + additional_cost, translation)
            )

    def clone(self):
        clone = Elider()
        clone.__src_nodes = self.__src_nodes
        return clone