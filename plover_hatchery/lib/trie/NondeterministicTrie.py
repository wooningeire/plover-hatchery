from collections import defaultdict
from collections.abc import Generator, Iterable, Sequence
from dataclasses import dataclass, field
import dataclasses

from plover_hatchery_lib_rs import (
    NondeterministicTrie as RsNondeterministicTrie,
    TransitionKey,
    TriePath,
    LookupResult,
    TransitionCostInfo,
    TransitionCostKey,
    ReverseTrieIndex as RsReverseTrieIndex,
    TransitionSourceNode,
    JoinedTriePaths,
    JoinedTransitionSeq,
    TransitionFlag,
    TransitionFlagManager,
)
from typing import Callable, Generator, final, override


class OnTraverse:
    def __call__(
        self,
        trie: "NondeterministicTrie",
        existing_trie_path: TriePath,
        new_transition: TransitionKey,
        /,
    ) -> bool: ...

@final
class NondeterministicTrie:
    """A trie that can be in multiple states at once. Delegates core operations to Rust."""

    ROOT = 0
    
    def __init__(self):
        self.rs = RsNondeterministicTrie()
        self.__on_try_traverse: list[OnTraverse] = []


    def follow(self, src_node_id: int, key_id: int | None, cost_info: TransitionCostInfo):
        """
        Gets the destination node obtained by following an existing transition associated with the given key
        from the given source node, or creates it if it does not exist. The node will not yet have been used by the current translation
        """
        return self.rs.follow(src_node_id, key_id, cost_info.cost, cost_info.translation_id)
    

    def follow_chain(self, src_node_id: int, key_ids: Sequence[int | None], cost_info: TransitionCostInfo):
        """
        Gets the destination node obtained by following the first existing transitions associated with the given series of keys
        from the given source node, or creates it (and any missing intermediate nodes) if it does not exist. Any nodes in the chain will
        not have bewen used by the current translation 
        """
        return self.rs.follow_chain(src_node_id, key_ids, cost_info.cost, cost_info.translation_id)


    def join(
        self,
        src_nodes: Iterable[TransitionSourceNode],
        key_ids_iter: Iterable[int | None],
        translation_id: int,
    ):
        return self.link_join(src_nodes, None, key_ids_iter, translation_id)


    def join_chain(
        self,
        src_nodes: Iterable[TransitionSourceNode],
        key_ids_iter: Iterable[Sequence[int | None]],
        translation_id: int,
    ):
        return self.link_join_chain(src_nodes, None, key_ids_iter, translation_id)


    def link_join(
        self,
        src_nodes: Iterable[TransitionSourceNode],
        dst_node: int | None,
        key_ids_iter: Iterable[int | None],
        translation_id: int,
    ):
        return self.rs.link_join(list(src_nodes), dst_node, list(key_ids_iter), translation_id)


    def link_join_chain(
        self,
        src_nodes: Iterable[TransitionSourceNode],
        dst_node: int | None,
        key_ids_iter: Iterable[Sequence[int | None]],
        translation_id: int,
    ):
        # Rust expects Vec<Vec<Option<usize>>>, so we need to ensure inner sequences are lists
        key_chains = [list(chain) for chain in key_ids_iter]
        return self.rs.link_join_chain(list(src_nodes), dst_node, key_chains, translation_id)


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
        
        # Convert to list to allow multiple iterations
        paths_list = list(src_node_paths)

        # If we have traverse handlers, we need to filter in Python
        if self.__on_try_traverse:
            results = self.rs.traverse(paths_list, key_id)
            
            for path in results:
                # Check the last transition against handlers
                if path.transitions:
                    last_transition = path.transitions[-1]
                    # Build the parent path (without the last transition)
                    parent_path = TriePath(last_transition.src_node_index, path.transitions[:-1])
                    if not self.__call_try_traverse_handlers(parent_path, last_transition):
                        continue
                yield path
        else:
            # Fast path: no handlers, just delegate to Rust
            yield from self.rs.traverse(paths_list, key_id)

    
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
    

    def link(self, src_node_id: int, dst_node_id: int, key_id: int | None, cost_info: TransitionCostInfo) -> TransitionKey:
        """
        Creates a transition from a given source node and key to an already-existing destination node
        """
        return self.rs.link(src_node_id, dst_node_id, key_id, cost_info.cost, cost_info.translation_id)

    
    def link_chain(self, src_node_id: int, dst_node_id: int, key_ids: Sequence[int | None], cost_info: TransitionCostInfo) -> list[TransitionKey]:
        """
        Follows all but the final transition from a given source node and series of keys, and then creates the final transition
        to the given already-existing destination node
        """
        return self.rs.link_chain(src_node_id, dst_node_id, key_ids, cost_info.cost, cost_info.translation_id)
    

    def set_translation(self, node_id: int, translation_id: int):
        self.rs.set_translation(node_id, translation_id)
        
    
    def get_translations_and_costs_single(self, node_id: int, transitions: Sequence[TransitionKey]):
        return self.rs.get_translations_and_costs_single(node_id, transitions)


    def get_translations_and_costs(self, node_paths: Sequence[TriePath]):
        return self.rs.get_translations_and_costs(node_paths)


    def get_translations_and_min_costs(self, node_paths: Sequence[TriePath]):
        return self.rs.get_translations_and_min_costs(node_paths)
    
    
    def transition_has_key(self, transition: TransitionKey, key_id: int | None):
        return self.rs.transition_has_key(transition, key_id)
    
    @override
    def __str__(self) -> str:
        n_nodes = self.rs.n_nodes()
        n_translations = len(self.rs.get_all_translation_ids())
        return f"NondeterministicTrie (Rust-backed): {n_nodes:,} nodes, {n_translations:,} translations"


    def build_reverse_lookup(self):
        reverse_index = self.rs.create_reverse_index()

        def get_sequences(translation_id: int) -> list[LookupResult]:
            return reverse_index.get_sequences(self.rs, translation_id)
        
        return get_sequences

    def build_subtrie_builder(self, transition_flags: TransitionFlagManager, get_key_str: Callable[[int | None], str]):
        reverse_index = self.rs.create_reverse_index()

        def build_subtrie(translation_id: int):
            raw_data = reverse_index.get_subtrie_data(self.rs, translation_id)
            if raw_data is None: return None
            
            processed_transitions = []
            for t in raw_data["transitions"]:
                src = t["src_node_id"]
                dst = t["dst_node_id"]
                keys_costs = []
                for key_id, idx, cost in t["key_infos"]:
                   key_str = get_key_str(key_id)
                   py_key = TransitionKey(src, key_id, idx)
                   cost_key = TransitionCostKey(py_key, translation_id)
                   flags = [transition_flags.get_label(flag) for flag in transition_flags.get_flags(cost_key)]
                   
                   keys_costs.append({
                       "key": key_str,
                       "cost": cost,
                       "flags": flags
                   })
                
                processed_transitions.append({
                    "src_node_id": src,
                    "dst_node_id": dst,
                    "keys_costs": keys_costs
                })
            
            return {
                "nodes": tuple(raw_data["nodes"]),
                "transitions": processed_transitions,
                "translation_nodes": raw_data["translation_nodes"]
            }
        
        return build_subtrie


    def get_transition_cost(self, transition: TransitionKey, translation_id: int):
        cost = self.rs.get_transition_cost(transition, translation_id)
        if cost is None:
            raise KeyError(f"pairing of translation {translation_id} and transition {transition} (key: {transition.key_id}) is not associated with a cost")
        return cost


    def get_transition_costs(self, transitions: Iterable[TransitionKey], translation_id: int):
        for transition in transitions:
            yield self.get_transition_cost(transition, translation_id)

    def profile(self):
        n_nodes = self.rs.n_nodes()
        n_translations = len(self.rs.get_all_translation_ids())
        return f"Rust-backed trie: {n_nodes:,} nodes, {n_translations:,} translations"