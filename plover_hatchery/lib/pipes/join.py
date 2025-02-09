from collections.abc import Iterable
from itertools import product
from dataclasses import dataclass

from plover.steno import Stroke

from ..trie import NondeterministicTrie, TransitionCostInfo


@dataclass(frozen=True)
class NodeSrc:
    node: int
    cost: int = 0


def join_chain(trie: NondeterministicTrie[str, str], src_nodes: Iterable[NodeSrc], key_sets: Iterable[tuple[str, ...]], translation: str):
    """Join all src_nodes along any stroke path"""

    products = product(src_nodes, key_sets)

    try:
        first_src_node, first_keys = next(products)
    except StopIteration:
        return None
    node = trie.get_first_dst_node_else_create_chain(first_src_node.node, first_keys, TransitionCostInfo(first_src_node.cost, translation))

    
    for src_node, keys in products:
        trie.link_chain(src_node.node, node, keys, TransitionCostInfo(src_node.cost, translation))


    return node

def join(trie: NondeterministicTrie[str, str], src_nodes: Iterable[NodeSrc], keys: Iterable[str], translation: str):
    return join_chain(trie, src_nodes, ((key,) for key in keys), translation)


def join_on_strokes(trie: NondeterministicTrie[str, str], src_nodes: Iterable[NodeSrc], strokes: Iterable[Stroke], translation: str):
    return join_chain(trie, src_nodes, (stroke.keys() for stroke in strokes), translation)


def tuplify(node: "int | None"):
    if node is None:
        return ()
    return (NodeSrc(node, 0),)