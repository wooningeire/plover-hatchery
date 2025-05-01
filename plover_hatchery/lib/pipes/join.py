from collections.abc import Iterable
from itertools import product
from dataclasses import dataclass
import dataclasses
from typing import final

from plover.steno import Stroke

from plover_hatchery.lib.trie import Transition, TriePath, TransitionKey

from ..trie import NondeterministicTrie, TransitionCostInfo


@final
@dataclass(frozen=True)
class NodeSrc:
    node: int
    cost: int = 0

    @staticmethod
    def increment_costs(srcs: "Iterable[NodeSrc]", cost_change: int):
        for src in srcs:
            yield dataclasses.replace(src, cost=src.cost + cost_change)


@final
@dataclass
class JoinedTransitionSeq:
    transitions: tuple[TransitionKey, ...]
    chord: Stroke


@final
@dataclass
class JoinedTriePaths:
    dst_node_id: "int | None"
    transition_seqs: tuple[JoinedTransitionSeq, ...]



def join_on_strokes(
    trie: NondeterministicTrie[str, int],
    src_nodes: Iterable[NodeSrc],
    strokes: Iterable[Stroke],
    entry_id: int,
):
    """Given a set of source nodes and a set of strokes, creates a common destination node from those source nodes when following any of the strokes."""

    products = product(src_nodes, strokes)

    try:
        first_src_node, first_stroke = next(products)
    except StopIteration:
        return JoinedTriePaths(None, ())

    transition_seqs: list[JoinedTransitionSeq] = []
    
    first_path = trie.follow_chain(first_src_node.node, first_stroke.keys(), TransitionCostInfo(first_src_node.cost, entry_id))
    
    transition_seqs.append(JoinedTransitionSeq(first_path.transitions, first_stroke))
    
    for src_node, stroke in products:
        transitions = trie.link_chain(src_node.node, first_path.dst_node_id, stroke.keys(), TransitionCostInfo(src_node.cost, entry_id))
        transition_seqs.append(JoinedTransitionSeq(transitions, stroke))

    return JoinedTriePaths(first_path.dst_node_id, tuple(transition_seqs))


def link_join_on_strokes(
    trie: NondeterministicTrie[str, int],
    src_nodes: Iterable[NodeSrc],
    dst_node: "int | None",
    strokes: Iterable[Stroke],
    entry_id: int,
):
    """
    Given a set of source nodes, a set of strokes, and a destination node, links all source nodes to the given destination node when following any of the strokes.
    Creates a new destination node if it is None.
    """

    if dst_node is None:
        return join_on_strokes(trie, src_nodes, strokes, entry_id)


    transition_seqs: list[JoinedTransitionSeq] = []

    for src_node, stroke in product(src_nodes, strokes):
        transitions = trie.link_chain(src_node.node, dst_node, stroke.keys(), TransitionCostInfo(src_node.cost, entry_id))
        transition_seqs.append(JoinedTransitionSeq(transitions, stroke))

    return JoinedTriePaths(dst_node, tuple(transition_seqs))


def tuplify(node: "int | None", cost: int=0):
    """Returns a tuple containing the node if it exists, or an empty tuple otherwise."""

    if node is None:
        return ()
    return (NodeSrc(node, cost),)