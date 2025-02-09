from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Generator, final

from .Trie import NondeterministicTrie, Transition


@final
@dataclass(frozen=True)
class TrieIndexLookupResult:
    cost: float
    transitions: tuple[Transition, ...]
    trie: NondeterministicTrie[str, str]


@final
class TrieIndexLookupState:
    def __init__(self, tries: dict[int, NondeterministicTrie[str, str]]):
        self.__tries = tries
        self.__nodes: dict[int, dict[int, tuple[Transition, ...]]] = {
            id(trie): {trie.ROOT: ()}
            for trie in tries.values()
        }


    def traverse(self, *keys: "str | tuple[str, ...]"):
        new_state: dict[int, dict[int, tuple[Transition, ...]]] = {}

        for trie_id, current_nodes in self.__nodes.items():
            trie = self.__tries[trie_id]

            new_nodes: dict[int, tuple[Transition, ...]] = {}
            for key in keys:
                if isinstance(key, str):
                    new_nodes.update(trie.get_dst_nodes(current_nodes, key))
                else:
                    new_nodes.update(trie.get_dst_nodes_chain(current_nodes, key))

            if len(new_nodes) == 0:
                continue
            
            new_state[trie_id] = new_nodes
        
        self.__nodes = new_state

    
    def get_translations(self):
        translations: dict[str, TrieIndexLookupResult] = {}

        for trie_id, current_nodes in self.__nodes.items():
            trie = self.__tries[trie_id]

            for translation, (cost, transitions) in trie.get_translations_and_costs(current_nodes).items():
                if translation in translations and cost >= translations[translation].cost: continue                    
                translations[translation] = TrieIndexLookupResult(cost, transitions, trie)

        return translations



@final
class TrieIndexReverseLookupState:
    def __init__(self, tries: dict[int, NondeterministicTrie[str, str]]):
        self.__tries = tries
        self.__reverse_lookups: dict[int, Callable[[str], Iterable[tuple[str, ...]]]] = {
            id(trie): trie.build_reverse_lookup()
            for trie in tries.values()
        }

    
    def reverse_lookup(self, translation: str) -> Generator[tuple[str, ...], None, None]:
        for reverse_lookup in self.__reverse_lookups.values():
            yield from reverse_lookup(translation)



@final
class TrieIndex:
    def __init__(self):
        self.__tries: dict[int, NondeterministicTrie[str, str]] = {}

    def add(self, trie: NondeterministicTrie[str, str]):
        self.__tries[id(trie)] = trie

    def create_lookup(self):
        return TrieIndexLookupState(self.__tries)

    def create_reverse_lookup(self):
        return TrieIndexReverseLookupState(self.__tries)

