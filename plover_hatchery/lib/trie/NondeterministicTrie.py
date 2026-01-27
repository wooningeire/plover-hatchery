from collections import defaultdict
from collections.abc import Generator, Iterable
from dataclasses import dataclass
import dataclasses
from itertools import product
from plover_hatchery.lib.trie.Transition import TransitionKey
from typing import TYPE_CHECKING, Any, Generator, Generic, Protocol, TypeVar, Union, final

from .Transition import TransitionKey, TransitionCostInfo, TransitionCostKey
from .LookupResult import LookupResult
from .TriePath import TriePath, JoinedTransitionSeq, JoinedTriePaths


_KeyVar = TypeVar("_KeyVar")

_Key = Union[_KeyVar, None]
_KeyId = Union[int, None]
"""None for epsilon (empty) transitions."""

class OnTraverse(Protocol[_KeyVar]):
    def __call__(
        self,
        trie: "NondeterministicTrie[_KeyVar]",
        existing_trie_path: TriePath,
        new_transition: TransitionKey,
        /,
    ) -> bool: ...


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
class NondeterministicTrie(Generic[_KeyVar]):
    """A trie that can be in multiple states at once."""

    ROOT = 0
    
    def __init__(self):
        self.__transitions: list[dict[_KeyId, list[int]]] = [{}]
        """Mapping from each node's id to its lists of destination nodes, based on the keys' ids"""
        self.__node_translations: dict[int, list[int]] = {}
        """Mapping from each node's id to its list of translation ids"""
        self.__keys: dict[_KeyVar, int] = {}
        """Mapping from each key to its id"""
        self.__transition_costs: dict[TransitionCostKey, float] = {}

        self.__keys_list: list[_KeyVar] = []

        self.__used_nodes_by_translation: dict[int, set[int]] = defaultdict(set)

        self.__on_try_traverse: list[OnTraverse[_KeyVar]] = []


    def follow(self, src_node_id: int, key: _Key[_KeyVar], cost_info: TransitionCostInfo):
        """
        Gets the destination node obtained by following an existing transition associated with the given key
        from the given source node, or creates it if it does not exist. The node will not yet have been used by the current translation
        """

        key_id = self.__get_key_id_else_create(key)
        translation_id = cost_info.translation_id


        # Reuse a node if it already exists and has not been used by this translation
        transitions = self.__transitions[src_node_id]
        if key_id in transitions:
            for transition_index, dst_node_id in enumerate(transitions[key_id]):
                if dst_node_id in self.__used_nodes_by_translation[translation_id]:
                    continue

                self.__used_nodes_by_translation[translation_id].add(dst_node_id)
                self.__assign_transition_cost(src_node_id, key_id, transition_index, cost_info)
                return TriePath(dst_node_id, (TransitionKey(src_node_id, key_id, transition_index),))
        
        # Create a new node
        new_node_id = self.__create_new_node()
        self.__used_nodes_by_translation[translation_id].add(new_node_id)
        if key_id in transitions:
            new_transition_index = len(transitions[key_id])
            transitions[key_id].append(new_node_id)
        else:
            new_transition_index = 0
            transitions[key_id] = [new_node_id]

        self.__assign_transition_cost(src_node_id, key_id, new_transition_index, cost_info)

        return TriePath(new_node_id, (TransitionKey(src_node_id, key_id, new_transition_index),))
    

    def follow_chain(self, src_node_id: int, keys: tuple[_Key[_KeyVar], ...], cost_info: TransitionCostInfo):
        """
        Gets the destination node obtained by following the first existing transitions associated with the given series of keys
        from the given source node, or creates it (and any missing intermediate nodes) if it does not exist. Any nodes in the chain will
        not have bewen used by the current translation 
        """

        current_node = src_node_id
        transitions: list[TransitionKey] = []

        for i, key in enumerate(keys):
            if i == len(keys) - 1: # Only assign the cost to the last transition
                path_addend = self.follow(current_node, key, cost_info)
            else: # but still assign a cost of 0 and associate the translation with the transition otherwise
                path_addend = self.follow(current_node, key, TransitionCostInfo(0, cost_info.translation_id))
            
            current_node = path_addend.dst_node_id
            transitions.append(path_addend.transitions[0])

        return TriePath(current_node, tuple(transitions))


    def join(
        self,
        src_nodes: Iterable[NodeSrc],
        keys_iter: Iterable[_KeyVar],
        translation_id: int,
    ):
        return self.join_chain(src_nodes, ((key,) for key in keys_iter), translation_id)


    def join_chain(
        self,
        src_nodes: Iterable[NodeSrc],
        keys_iter: Iterable[tuple[_KeyVar, ...]],
        translation_id: int,
    ):
        """Given a set of source nodes and a set of keys, creates a common destination node from those source nodes when following any of the keys."""

        products = product(src_nodes, keys_iter)

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
        keys_iter: Iterable[_KeyVar],
        translation_id: int,
    ):
        return self.link_join_chain(src_nodes, dst_node, ((key,) for key in keys_iter), translation_id)


    def link_join_chain(
        self,
        src_nodes: Iterable[NodeSrc],
        dst_node: int | None,
        keys_iter: Iterable[tuple[_KeyVar, ...]],
        translation_id: int,
    ):
        """
        Given a set of source nodes, a set of strokes, and a destination node, links all source nodes to the given destination node when following any of the strokes.
        Creates a new destination node if it is None.
        """

        if dst_node is None:
            return self.join_chain(src_nodes, keys_iter, translation_id)


        transition_seqs: list[JoinedTransitionSeq] = []

        for src_node, keys in product(src_nodes, keys_iter):
            transitions = self.link_chain(src_node.node, dst_node, keys, TransitionCostInfo(src_node.cost, translation_id))
            transition_seqs.append(JoinedTransitionSeq(transitions))

        return JoinedTriePaths(dst_node, tuple(transition_seqs))


    def __call_try_traverse_handlers(self, trie_path: TriePath, transition: TransitionKey):
        return all(handler(self, trie_path, transition) for handler in self.__on_try_traverse)
            

    def on_check_traverse(self, handler: OnTraverse[_KeyVar]):
        self.__on_try_traverse.append(handler)


    def traverse(self, src_node_paths: Iterable[TriePath], key: _KeyVar) -> Generator[TriePath, None, None]:
        """
        Gets the destination nodes obtained by following all existing transitions associated with the given key from the given set of
        source nodes

        :param src_nodes: A dictionary mapping source node IDs to the sequences of Transitions followed to get to those nodes
        :returns: A dictionary mapping destination IDs to the updated sequences of Transitions followed to get to those nodes
        """

        key_id = self.__keys.get(key)
        if key_id is None:
            return
        
        for path in src_node_paths:
            transitions = self.__transitions[path.dst_node_id]
            if key_id not in transitions:
                continue

            for transition_index, dst_node_id in enumerate(self.__transitions[path.dst_node_id][key_id]):
                transition_key = TransitionKey(path.dst_node_id, key_id, transition_index)
                if not self.__call_try_traverse_handlers(path, transition_key): continue

                yield from self.__dfs_empty_transitions(
                    TriePath(dst_node_id, path.transitions + (transition_key,)),
                    set(),
                )

    
    def traverse_chain(self, src_node_paths: Iterable[TriePath], keys: tuple[_KeyVar, ...]) -> Iterable[TriePath]:
        """
        Gets the destination nodes obtained by following all existing transitions associated with the given series of keys from the given set of
        source nodes

        :param src_nodes: A dictionary mapping source node IDs to the sequences of Transitions followed to get to those nodes
        :returns: A dictionary mapping destination IDs to the updated sequences of Transitions followed to get to those nodes
        """

        current_nodes = src_node_paths
        for key in keys:
            current_nodes = self.traverse(current_nodes, key)
        return current_nodes

    
    def __dfs_empty_transitions(self, src_node_path: TriePath, visited_transitions: set[TransitionKey]) -> Generator[TriePath, None, None]:
        yield src_node_path

        transitions = self.__transitions[src_node_path.dst_node_id]
        if None not in transitions:
            return

        for transition_index, dst_node_id in enumerate(self.__transitions[src_node_path.dst_node_id][None]):
            transition_key = TransitionKey(src_node_path.dst_node_id, None, transition_index)
            if transition_key in visited_transitions:
                continue

            if not self.__call_try_traverse_handlers(src_node_path, transition_key): continue

            yield from self.__dfs_empty_transitions(
                TriePath(dst_node_id, src_node_path.transitions + (transition_key,)),
                visited_transitions | {transition_key},
            )
    

    def link(self, src_node_id: int, dst_node_id: int, key: _Key[_KeyVar], cost_info: TransitionCostInfo):
        """
        Creates a transition from a given source node and key to an already-existing destination node
        """

        key_id = self.__get_key_id_else_create(key)

        dst_dict = self.__transitions[src_node_id]
        
        if key_id in dst_dict:
            dst_node_ids = dst_dict[key_id]

            if dst_node_id in dst_node_ids: # Is there already a transition between these two nodes with this key? If so, use that
                transition_index = dst_node_ids.index(dst_node_id)
            else: # Otherwise, create the link
                transition_index = len(self.__transitions[src_node_id][key_id])
                dst_dict[key_id].append(dst_node_id)
        else: 
            transition_index = 0
            dst_dict[key_id] = [dst_node_id]

        self.__assign_transition_cost(src_node_id, key_id, transition_index, cost_info)

        return TransitionKey(src_node_id, key_id, transition_index)

    
    def link_chain(self, src_node_id: int, dst_node_id: int, keys: tuple[_Key[_KeyVar], ...], cost_info: TransitionCostInfo) -> tuple[TransitionKey, ...]:
        """
        Follows all but the final transition from a given source node and series of keys, and then creates the final transition
        to the given already-existing destination node
        """
        path = self.follow_chain(src_node_id, keys[:-1], TransitionCostInfo(0, cost_info.translation_id))

        transition = self.link(path.dst_node_id, dst_node_id, keys[-1], cost_info)

        return path.transitions + (transition,)
    

    def set_translation(self, node_id: int, translation_id: int):
        if node_id in self.__node_translations:
            self.__node_translations[node_id].append(translation_id)
        else:
            self.__node_translations[node_id] = [translation_id]
        
    
    def get_translations_and_costs_single(self, node_id: int, transitions: Iterable[TransitionKey]):
        if node_id not in self.__node_translations:
            return
        
        for translation_id in self.__node_translations[node_id]:
            is_valid_path = True
            cumsum_cost = 0
            for transition in transitions:
                key = TransitionCostKey(transition, translation_id)
                if key not in self.__transition_costs:
                    is_valid_path = False
                    break
                
                cumsum_cost += self.__transition_costs[key]

            if not is_valid_path:
                continue

            yield (translation_id, cumsum_cost)


    def get_translations_and_costs(self, node_paths: Iterable[TriePath]):
        for path in node_paths:
            for translation_id, cost in self.get_translations_and_costs_single(path.dst_node_id, path.transitions):
                yield LookupResult(translation_id, cost, path.transitions)


    def get_translations_and_min_costs(self, node_paths: Iterable[TriePath]):
        min_cost_results: dict[int, tuple[int, float, tuple[TransitionKey, ...]]] = {}
        for path in node_paths:
            for translation_id, cost in self.get_translations_and_costs_single(path.dst_node_id, path.transitions):
                if cost >= min_cost_results.get(translation_id, (float("inf"), None))[0]: continue
                min_cost_results[translation_id] = (translation_id, cost, path.transitions)

        for translation_id, cost, transitions in min_cost_results.values():
            yield LookupResult(translation_id, cost, transitions)
    
    
    def transition_has_key(self, transition: TransitionKey, key: _Key[_KeyVar]):
        if key is None:
            return transition.key_id is None

        return self.__keys[key] == transition.key_id
    
    def __str__(self):
        lines: list[str] = []

        transition_costs: dict[TransitionKey, dict[int, float]] = {}
        for (transition, translation_id), cost in self.__transition_costs.items():
            if transition in transition_costs:
                transition_costs[transition][translation_id] = cost
                continue

            transition_costs[transition] = {translation_id: cost}

        for i, transitions in enumerate(self.__transitions):
            translation_ids = self.__node_translations.get(i)
            lines.append(f"""Node {i}{f" : {tuple(translation_ids)}" if translation_ids is not None else ""}""")

            for key_id, dst_node_ids in transitions.items():
                lines.append(f"""  On {self.get_key_str(key_id)} goto {",".join(str(node) for node in dst_node_ids)}""")

                for j, dst_nodes in enumerate(dst_node_ids):
                    if TransitionKey(i, key_id, j) not in transition_costs: continue
                    lines.append(f"""    {dst_nodes} valid for:""")

                    for translation_id, cost in transition_costs[TransitionKey(i, key_id, j)].items():
                        lines.append(f"""      translation {translation_id} (cost {cost})""")

        return "\n".join(lines)

    def to_json(self):
        return {
            "transitions": self.__transitions,
            "keys": self.__keys_list,
            "node_translations": self.__node_translations,
            "transition_costs": [
                {
                    "transition": {
                        "src_node_index": cost_key.transition.src_node_index,
                        "transition_index": cost_key.transition.transition_index,
                        "key_id": cost_key.transition.key_id,
                    },
                    "translation_id": cost_key.translation_id,
                    "cost": cost,
                }
                for cost_key, cost in self.__transition_costs.items()
            ],
        }
    
#     def optimized(self: "NondeterministicTrie[str, int]"):
#         new_trie: NondeterministicTrie[str, int] = NondeterministicTrie()
#         self.__transfer_node_and_descendants_if_necessary(new_trie, self.ROOT, {0: 0}, Stroke.from_keys(()), set(), {0}, self.__key_ids_to_keys())
# #         plover.log.debug(f"""

# # Optimized lookup trie.
# # \t{self.profile()}
# # \t\t->
# # \t{new_trie.profile()}
# # """)
#         return new_trie
    

    # def profile(self):
    #     from pympler.asizeof import asizeof
    #     n_transitions = sum(sum(len(dst_nodes) for dst_nodes in transitions.values()) for transitions in self.__nodes)
    #     return f"{len(self.__nodes):,} nodes, {n_transitions:,} transitions, {len(self.__translations):,} translations ({asizeof(self):,} bytes)"
    
    # def frozen(self):
    #     return ReadonlyNondeterministicTrie(self.__nodes, self.__translations, self.__keys)
    
    def __get_key_id_else_create(self, key: _Key[_KeyVar]):
        if key is None:
            return None

        if key in self.__keys:
            return self.__keys[key]
        
        new_key_id = len(self.__keys)
        self.__keys[key] = new_key_id
        self.__keys_list.append(key)
        return new_key_id

    def __create_new_node(self):
        new_node_id = len(self.__transitions)
        self.__transitions.append({})
        return new_node_id
    
    def __assign_transition_cost(self, src_node_id: int, key_id: _KeyId, new_transition_index: int, cost_info: TransitionCostInfo | None):
        if cost_info is None: return
        cost_key = TransitionCostKey(
            TransitionKey(src_node_id, key_id, new_transition_index),
            cost_info.translation_id
        )
        self.__transition_costs[cost_key] = min(cost_info.cost, self.__transition_costs.get(cost_key, float("inf")))
    
    def __transition_has_cost_for_translation(self, src_node_id: int, key_id: _KeyId, new_transition_index: int, translation_id: int):
        cost_key = TransitionCostKey(
            TransitionKey(src_node_id, key_id, new_transition_index),
            translation_id
        )
        return cost_key in self.__transition_costs

    def __reversed_nodes(self):
        reverse_nodes: dict[int, dict[_KeyId, list[tuple[int, int]]]] = defaultdict(lambda: defaultdict(list))
        for src_node_id, transitions in enumerate(self.__transitions):
            for key_id, dst_node_ids in transitions.items():
                for i, dst_node_id in enumerate(dst_node_ids):
                    reverse_nodes[dst_node_id][key_id].append((src_node_id, i))

        return reverse_nodes

    def __reversed_translations(self):
        reverse_translations: dict[int, list[int]] = defaultdict(list)
        for node, translation_ids in self.__node_translations.items():
            for translation_id in translation_ids:
                reverse_translations[translation_id].append(node)

        return reverse_translations

    def build_reverse_lookup(self):
        reverse_nodes = self.__reversed_nodes()
        reverse_translations = self.__reversed_translations()


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
            
            for key_id, src_nodes in reverse_nodes[node].items():
                for src_node_id, transition_index in src_nodes:
                    if src_node_id in visited_nodes: continue

                    if not self.__transition_has_cost_for_translation(src_node_id, key_id, transition_index, translation_id):
                        continue

                    transition_key = TransitionKey(src_node_id, key_id, transition_index)
                    transition_cost_key = TransitionCostKey(transition_key, translation_id)

                    yield from dfs(
                        src_node_id,
                        translation_id,
                        transitions_reversed + (transition_key,),
                        cost + self.__transition_costs[transition_cost_key],
                        visited_nodes | {src_node_id},
                    )

        def get_sequences(translation_id: int) -> Generator[LookupResult, None, None]:
            if translation_id not in reverse_translations: return
            
            for node in reverse_translations[translation_id]:
                for transitions_reversed, cost in dfs(node, translation_id, (), 0, {node}):
                    yield LookupResult(translation_id, cost, tuple(reversed(transitions_reversed)))
        
        return get_sequences

    def build_subtrie_builder(self):
        reverse_nodes = self.__reversed_nodes()
        reverse_translations = self.__reversed_translations()


        visited_nodes = set[int]()
        nodes_toposort: list[int] = []
        visited_transitions = defaultdict[tuple[int, int], set[int | None]](set)

        def dfs(node: int, translation_id: int):
            if node in visited_nodes: return

            visited_nodes.add(node)

            for key_id, src_nodes in reverse_nodes[node].items():
                for src_node_id, transition_index in src_nodes:
                    if not self.__transition_has_cost_for_translation(src_node_id, key_id, transition_index, translation_id):
                        continue

                    dfs(src_node_id, translation_id)

                    visited_transitions[(src_node_id, node)].add(key_id)


            # add at end to obtain a topological sort
            nodes_toposort.append(node)


        def build_subtrie(translation_id: int):
            """Constructs a nondeterministic trie consisting of only the nodes and transitions that may lead to the given translation_id."""

            if translation_id not in reverse_translations: return None
            
            for node in reverse_translations[translation_id]:
                dfs(node, translation_id)

            result = {
                "nodes": tuple(nodes_toposort),
                "transitions": [
                    {
                        "src_node_id": src_node_id,
                        "dst_node_id": dst_node_id,
                        "keys": [self.get_key_str(key_id) for key_id in key_ids],
                    }
                    for (src_node_id, dst_node_id), key_ids in visited_transitions.items()
                ],
            }

            visited_nodes.clear()
            nodes_toposort.clear()
            visited_transitions.clear()

            return result
                    
        
        return build_subtrie


    def get_transition_cost(self, transition: TransitionKey, translation_id: int):
        cost_key = TransitionCostKey(
            transition,
            translation_id,
        )
        if cost_key not in self.__transition_costs:
            raise KeyError(f"pairing of translation {translation_id} and transition {transition} (key: {self.get_key_str(transition.key_id)}) is not associated with a cost")
    
        return self.__transition_costs[cost_key]


    def get_transition_costs(self, transitions: Iterable[TransitionKey], translation_id: int):
        for transition in transitions:
            yield self.get_transition_cost(transition, translation_id)

        
    def get_key(self, key_id: int):
        return self.__keys_list[key_id]

        
    def get_key_str(self, key_id: _KeyId):
        if key_id is None:
            return "(ε)"

        return str(self.__keys_list[key_id])

    def profile(self):
#         from pympler.asizeof import asizeof
        n_nodes = len(self.__transitions)
        n_transitions = sum(len(dst_nodes) for dst_nodes in self.__transitions)
#         return f"{n_nodes:,} nodes, {n_transitions:,} transitions, {len(self.__translations):,} translations ({asizeof(self):,} bytes)"
        return f"{n_nodes:,} nodes, {n_transitions:,} transitions, {len(self.__node_translations):,} translations"