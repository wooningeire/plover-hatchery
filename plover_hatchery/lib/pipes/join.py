from typing import Iterable
from itertools import product

from plover.steno import Stroke

from ..trie import NondeterministicTrie, TransitionCostInfo


def join_chain(trie: NondeterministicTrie[str, str], src_nodes: Iterable[int], key_sets: Iterable[tuple[str, ...]], translation: str):
    """Join all src_nodes along any stroke path"""

    products = product(src_nodes, key_sets)

    try:
        first_src_node, first_keys = next(products)
    except StopIteration:
        return None
    node = trie.get_first_dst_node_else_create_chain(first_src_node, first_keys, TransitionCostInfo(0, translation))

    
    for src_node, keys in products:
        trie.link_chain(src_node, node, keys, TransitionCostInfo(0, translation))


    return node

def join(trie: NondeterministicTrie[str, str], src_nodes: Iterable[int], keys: Iterable[str], translation: str):
    return join_chain(trie, src_nodes, ((key,) for key in keys), translation)


def join_on_strokes(trie: NondeterministicTrie[str, str], src_nodes: Iterable[int], strokes: Iterable[Stroke], translation: str):
    return join_chain(trie, src_nodes, (stroke.keys() for stroke in strokes), translation)


def tuplify(node: "int | None"):
    if node is None:
        return ()
    return (node,)