from collections.abc import Iterable
from itertools import product
from dataclasses import dataclass

from plover.steno import Stroke

from ..trie import NondeterministicTrie, TransitionCostInfo


@dataclass(frozen=True)
class NodeSrc:
    node: int
    cost: int = 0


def join_chain(trie: NondeterministicTrie[str, int], src_nodes: Iterable[NodeSrc], key_sets: Iterable[tuple[str, ...]], entry_id: int):
    """Join all src_nodes along any stroke path"""

    products = product(src_nodes, key_sets)

    try:
        first_src_node, first_keys = next(products)
    except StopIteration:
        return None
    node = trie.get_first_dst_node_else_create_chain(first_src_node.node, first_keys, TransitionCostInfo(first_src_node.cost, entry_id))

    
    for src_node, keys in products:
        trie.link_chain(src_node.node, node, keys, TransitionCostInfo(src_node.cost, entry_id))


    return node

def join(trie: NondeterministicTrie[str, int], src_nodes: Iterable[NodeSrc], keys: Iterable[str], entry_id: int):
    return join_chain(trie, src_nodes, ((key,) for key in keys), entry_id)


def join_on_strokes(trie: NondeterministicTrie[str, int], src_nodes: Iterable[NodeSrc], strokes: Iterable[Stroke], entry_id: int):
    return join_chain(trie, src_nodes, (stroke.keys() for stroke in strokes), entry_id)


def tuplify(node: "int | None"):
    if node is None:
        return ()
    return (NodeSrc(node, 0),)