from collections import defaultdict
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
import dataclasses
from itertools import product
from plover_hatchery_lib_rs import (
    NondeterministicTrie as RsNondeterministicTrie,
    TransitionKey as RsTransitionKey,
    TriePath as RsTriePath,
    LookupResult as RsLookupResult,
)
from typing import TYPE_CHECKING, Any, Callable, Generator, Generic, Protocol, TypeVar, Union, final, override

from .Transition import TransitionKey, TransitionCostInfo, TransitionCostKey
from .LookupResult import LookupResult
from .TriePath import TriePath, JoinedTransitionSeq, JoinedTriePaths


def _py_transition_key(rs_key: RsTransitionKey) -> TransitionKey:
    """Convert Rust TransitionKey to Python TransitionKey."""
    return TransitionKey(rs_key.src_node_index, rs_key.key_id, rs_key.transition_index)


def _rs_transition_key(py_key: TransitionKey) -> RsTransitionKey:
    """Convert Python TransitionKey to Rust TransitionKey."""
    return RsTransitionKey(py_key.src_node_index, py_key.key_id, py_key.transition_index)


def _py_trie_path(rs_path: RsTriePath) -> TriePath:
    """Convert Rust TriePath to Python TriePath."""
    return TriePath(
        rs_path.dst_node_id,
        tuple(_py_transition_key(t) for t in rs_path.transitions),
    )


def _rs_trie_path(py_path: TriePath) -> RsTriePath:
    """Convert Python TriePath to Rust TriePath."""
    return RsTriePath(
        py_path.dst_node_id,
        [_rs_transition_key(t) for t in py_path.transitions],
    )


def _py_lookup_result(rs_result: RsLookupResult) -> LookupResult:
    """Convert Rust LookupResult to Python LookupResult."""
    return LookupResult(
        rs_result.translation_id,
        rs_result.cost,
        tuple(_py_transition_key(t) for t in rs_result.transitions),
    )


class OnTraverse:
    def __call__(
        self,
        trie: "NondeterministicTrie",
        existing_trie_path: TriePath,
        new_transition: TransitionKey,
        /,
    ) -> bool: ...


@final
@dataclass(frozen=True)
class TransitionFlag:
    label: str

@final
@dataclass(frozen=True)
class NodeSrc:
    node: int
    cost: int = 0
    outgoing_transition_flags: tuple[TransitionFlag, ...] = ()

    @staticmethod
    def increment_costs(srcs: "Iterable[NodeSrc]", cost_change: int):
        for src in srcs:
            yield dataclasses.replace(src, cost=src.cost + cost_change)

    @staticmethod
    def add_flags(srcs: "Iterable[NodeSrc]", flags: tuple[TransitionFlag, ...]):
        for src in srcs:
            yield dataclasses.replace(src, outgoing_transition_flags=src.outgoing_transition_flags + flags)

@final
class TransitionFlagManager:
    def __init__(self):
        self.mappings = defaultdict[TransitionCostKey, list[TransitionFlag]](list)
        self.flag_types = set[TransitionFlag]()

@final
class NondeterministicTrie:
    """A trie that can be in multiple states at once. Delegates core operations to Rust."""

    ROOT = 0
    
    def __init__(self):
        self.__rs = RsNondeterministicTrie()
        
        # Keep Python state for features not yet in Rust
        self.__transition_costs: dict[TransitionCostKey, float] = {}
        self.__on_try_traverse: list[OnTraverse] = []


    def follow(self, src_node_id: int, key_id: int | None, cost_info: TransitionCostInfo):
        """
        Gets the destination node obtained by following an existing transition associated with the given key
        from the given source node, or creates it if it does not exist. The node will not yet have been used by the current translation
        """
        rs_path = self.__rs.follow(src_node_id, key_id, cost_info.cost, cost_info.translation_id)
        
        # Track cost in Python for features that need it
        if rs_path.transitions:
            rs_key = rs_path.transitions[0]
            py_key = _py_transition_key(rs_key)
            cost_key = TransitionCostKey(py_key, cost_info.translation_id)
            self.__transition_costs[cost_key] = min(cost_info.cost, self.__transition_costs.get(cost_key, float("inf")))
        
        return _py_trie_path(rs_path)
    

    def follow_chain(self, src_node_id: int, key_ids: tuple[int | None, ...], cost_info: TransitionCostInfo):
        """
        Gets the destination node obtained by following the first existing transitions associated with the given series of keys
        from the given source node, or creates it (and any missing intermediate nodes) if it does not exist. Any nodes in the chain will
        not have bewen used by the current translation 
        """
        rs_path = self.__rs.follow_chain(src_node_id, list(key_ids), cost_info.cost, cost_info.translation_id)
        
        # Track costs in Python
        py_path = _py_trie_path(rs_path)
        for i, py_key in enumerate(py_path.transitions):
            # Only the last transition gets the full cost
            trans_cost = cost_info.cost if i == len(py_path.transitions) - 1 else 0
            cost_key = TransitionCostKey(py_key, cost_info.translation_id)
            self.__transition_costs[cost_key] = min(trans_cost, self.__transition_costs.get(cost_key, float("inf")))
        
        return py_path


    def join(
        self,
        src_nodes: Iterable[NodeSrc],
        key_ids_iter: Iterable[int | None],
        translation_id: int,
    ):
        return self.join_chain(src_nodes, ((key_id,) for key_id in key_ids_iter), translation_id)


    def join_chain(
        self,
        src_nodes: Iterable[NodeSrc],
        key_ids_iter: Iterable[tuple[int | None, ...]],
        translation_id: int,
    ):
        """Given a set of source nodes and a set of keys, creates a common destination node from those source nodes when following any of the keys."""

        products = product(src_nodes, key_ids_iter)

        try:
            first_src, first_keys = next(products)
        except StopIteration:
            return JoinedTriePaths(None, ())

        transition_seqs: list[JoinedTransitionSeq] = []
        
        first_path = self.follow_chain(first_src.node, first_keys, TransitionCostInfo(first_src.cost, translation_id))
        
        transition_seqs.append(JoinedTransitionSeq(first_path.transitions))
        
        for src, keys in products:
            transitions = self.link_chain(src.node, first_path.dst_node_id, keys, TransitionCostInfo(src.cost, translation_id))
            transition_seqs.append(JoinedTransitionSeq(transitions))

        return JoinedTriePaths(first_path.dst_node_id, tuple(transition_seqs))


    def link_join(
        self,
        src_nodes: Iterable[NodeSrc],
        dst_node: int | None,
        key_ids_iter: Iterable[int | None],
        translation_id: int,
    ):
        return self.link_join_chain(src_nodes, dst_node, ((key_id,) for key_id in key_ids_iter), translation_id)


    def link_join_chain(
        self,
        src_nodes: Iterable[NodeSrc],
        dst_node: int | None,
        key_ids_iter: Iterable[tuple[int | None, ...]],
        translation_id: int,
    ):
        """
        Given a set of source nodes, a set of strokes, and a destination node, links all source nodes to the given destination node when following any of the strokes.
        Creates a new destination node if it is None.
        """

        if dst_node is None:
            return self.join_chain(src_nodes, key_ids_iter, translation_id)


        transition_seqs: list[JoinedTransitionSeq] = []

        for src_node, key_ids in product(src_nodes, key_ids_iter):
            transitions = self.link_chain(src_node.node, dst_node, key_ids, TransitionCostInfo(src_node.cost, translation_id))
            transition_seqs.append(JoinedTransitionSeq(transitions))

        return JoinedTriePaths(dst_node, tuple(transition_seqs))


    def __call_try_traverse_handlers(self, trie_path: TriePath, transition: TransitionKey):
        return all(handler(self, trie_path, transition) for handler in self.__on_try_traverse)
            

    def on_check_traverse(self, handler: OnTraverse):
        self.__on_try_traverse.append(handler)


    def traverse(self, src_node_paths: Iterable[TriePath], key_id: int | None) -> Generator[TriePath, None, None]:
        """
        Gets the destination nodes obtained by following all existing transitions associated with the given key from the given set of
        source nodes

        :param src_nodes: A dictionary mapping source node IDs to the sequences of Transitions followed to get to those nodes
        :returns: A dictionary mapping destination IDs to the updated sequences of Transitions followed to get to those nodes
        """

        if key_id is None:
            return
        
        # If we have traverse handlers, we need to filter in Python
        if self.__on_try_traverse:
            # Convert to list to allow multiple iterations
            paths_list = list(src_node_paths)
            rs_paths = [_rs_trie_path(p) for p in paths_list]
            rs_results = self.__rs.traverse(rs_paths, key_id)
            
            for rs_path in rs_results:
                py_path = _py_trie_path(rs_path)
                # Check the last transition against handlers
                if py_path.transitions:
                    last_transition = py_path.transitions[-1]
                    # Build the parent path (without the last transition)
                    parent_path = TriePath(last_transition.src_node_index, py_path.transitions[:-1])
                    if not self.__call_try_traverse_handlers(parent_path, last_transition):
                        continue
                yield py_path
        else:
            # Fast path: no handlers, just delegate to Rust
            rs_paths = [_rs_trie_path(p) for p in src_node_paths]
            for rs_path in self.__rs.traverse(rs_paths, key_id):
                yield _py_trie_path(rs_path)

    
    def traverse_chain(self, src_node_paths: Iterable[TriePath], key_ids: tuple[int | None, ...]) -> Iterable[TriePath]:
        """
        Gets the destination nodes obtained by following all existing transitions associated with the given series of keys from the given set of
        source nodes

        :param src_nodes: A dictionary mapping source node IDs to the sequences of Transitions followed to get to those nodes
        :returns: A dictionary mapping destination IDs to the updated sequences of Transitions followed to get to those nodes
        """

        current_nodes = src_node_paths
        for key_id in key_ids:
            current_nodes = self.traverse(current_nodes, key_id)
        return current_nodes
    

    def link(self, src_node_id: int, dst_node_id: int, key_id: int | None, cost_info: TransitionCostInfo):
        """
        Creates a transition from a given source node and key to an already-existing destination node
        """
        rs_key = self.__rs.link(src_node_id, dst_node_id, key_id, cost_info.cost, cost_info.translation_id)
        py_key = _py_transition_key(rs_key)
        
        # Track cost in Python
        cost_key = TransitionCostKey(py_key, cost_info.translation_id)
        self.__transition_costs[cost_key] = min(cost_info.cost, self.__transition_costs.get(cost_key, float("inf")))
        
        return py_key

    
    def link_chain(self, src_node_id: int, dst_node_id: int, key_ids: tuple[int | None, ...], cost_info: TransitionCostInfo) -> tuple[TransitionKey, ...]:
        """
        Follows all but the final transition from a given source node and series of keys, and then creates the final transition
        to the given already-existing destination node
        """
        rs_keys = self.__rs.link_chain(src_node_id, dst_node_id, list(key_ids), cost_info.cost, cost_info.translation_id)
        py_keys = tuple(_py_transition_key(k) for k in rs_keys)
        
        # Track costs in Python
        for i, py_key in enumerate(py_keys):
            trans_cost = cost_info.cost if i == len(py_keys) - 1 else 0
            cost_key = TransitionCostKey(py_key, cost_info.translation_id)
            self.__transition_costs[cost_key] = min(trans_cost, self.__transition_costs.get(cost_key, float("inf")))
        
        return py_keys
    

    def set_translation(self, node_id: int, translation_id: int):
        self.__rs.set_translation(node_id, translation_id)
        
    
    def get_translations_and_costs_single(self, node_id: int, transitions: Iterable[TransitionKey]):
        rs_transitions = [_rs_transition_key(t) for t in transitions]
        for translation_id, cost in self.__rs.get_translations_and_costs_single(node_id, rs_transitions):
            yield (translation_id, cost)


    def get_translations_and_costs(self, node_paths: Iterable[TriePath]):
        rs_paths = [_rs_trie_path(p) for p in node_paths]
        for rs_result in self.__rs.get_translations_and_costs(rs_paths):
            yield _py_lookup_result(rs_result)


    def get_translations_and_min_costs(self, node_paths: Iterable[TriePath]):
        min_cost_results: dict[int, tuple[int, float, tuple[TransitionKey, ...]]] = {}
        for path in node_paths:
            for translation_id, cost in self.get_translations_and_costs_single(path.dst_node_id, path.transitions):
                if cost >= min_cost_results.get(translation_id, (float("inf"), None))[0]: continue
                min_cost_results[translation_id] = (translation_id, cost, path.transitions)

        for translation_id, cost, transitions in min_cost_results.values():
            yield LookupResult(translation_id, cost, transitions)
    
    
    def transition_has_key(self, transition: TransitionKey, key_id: int | None):
        return self.__rs.transition_has_key(_rs_transition_key(transition), key_id)
    
    @override
    def __str__(self) -> str:
        lines: list[str] = []

        transition_costs: dict[TransitionKey, dict[int, float]] = {}
        for (transition, translation_id), cost in self.__transition_costs.items():
            if transition in transition_costs:
                transition_costs[transition][translation_id] = cost
                continue

            transition_costs[transition] = {translation_id: cost}

        # Note: This uses Python-side costs for display
        lines.append(f"NondeterministicTrie (Rust-backed)")
        lines.append(f"  Transition costs tracked: {len(self.__transition_costs)}")

        return "\n".join(lines)
    

    def __transition_has_cost_for_translation(self, src_node_id: int, key_id: int | None, new_transition_index: int, translation_id: int):
        cost_key = TransitionCostKey(
            TransitionKey(src_node_id, key_id, new_transition_index),
            translation_id
        )
        return cost_key in self.__transition_costs

    def __reversed_translations(self):
        # This needs access to node_translations which is in Rust
        # For now, we track this in Python as well via transition_costs
        reverse_translations: dict[int, list[int]] = defaultdict(list)
        seen_pairs: set[tuple[int, int]] = set()
        
        for cost_key in self.__transition_costs:
            translation_id = cost_key.translation_id
            # We need to find nodes that have translations - this is a limitation
            # For now, return empty since we'd need to query Rust
        
        return reverse_translations

    def build_reverse_lookup(self):
        # This feature requires access to internal Rust state that's not exposed yet
        # Keep using Python-side costs for now
        
        def dfs(
            node: int,
            translation_id: int,
            transitions_reversed: tuple[TransitionKey, ...],
            cost: float,
            visited_nodes: set[int],
        ) -> Generator[tuple[tuple[TransitionKey, ...], float], None, None]:
            if node == self.ROOT:
                yield transitions_reversed, cost
                return
            
            # This needs reverse node lookup which requires internal Rust state
            # For now, yield nothing
            return

        def get_sequences(translation_id: int) -> Generator[LookupResult, None, None]:
            # Limited implementation - requires full Rust integration
            return
            yield  # Make it a generator
        
        return get_sequences

    def build_subtrie_builder(self, transition_flags: TransitionFlagManager, get_key_str: Callable[[int | None], str]):
        # This feature requires access to internal Rust state that's not exposed yet
        raise NotImplementedError("build_subtrie_builder requires full Rust integration - not yet implemented")


    def get_transition_cost(self, transition: TransitionKey, translation_id: int):
        cost = self.__rs.get_transition_cost(_rs_transition_key(transition), translation_id)
        if cost is None:
            raise KeyError(f"pairing of translation {translation_id} and transition {transition} (key: {transition.key_id}) is not associated with a cost")
        return cost


    def get_transition_costs(self, transitions: Iterable[TransitionKey], translation_id: int):
        for transition in transitions:
            yield self.get_transition_cost(transition, translation_id)

    def profile(self):
        n_costs = len(self.__transition_costs)
        return f"Rust-backed trie with {n_costs:,} tracked transition costs"