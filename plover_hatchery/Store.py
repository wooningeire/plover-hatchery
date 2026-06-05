from threading import RLock
from typing import Any, Callable, Protocol, final

from plover_hatchery.lib.trie.NondeterministicTrie import NondeterministicTrie


class CompilableHatcheryDictionary(Protocol):
    def compile(self, *, refresh_cache: bool=False) -> dict[str, Any]: ...


@final
class Store:
    def __init__(self):
        self.breakdown_translation: Callable[[str], str | None] | None = None
        self.breakdown_lookup: Callable[[tuple[str, ...], list[str]], str | None] | None = None
        self.trie: NondeterministicTrie | None = None
        self.translations: list[str] | None = None
        self.hatchery_dictionaries: dict[str, CompilableHatcheryDictionary] = {}
        self.__hatchery_compile_lock = RLock()

    def register_hatchery_dictionary(self, path: str, dictionary: CompilableHatcheryDictionary):
        with self.__hatchery_compile_lock:
            self.hatchery_dictionaries[path] = dictionary

    def compile_hatchery_dictionaries(self, *, refresh_cache: bool=False):
        with self.__hatchery_compile_lock:
            return [
                dictionary.compile(refresh_cache=refresh_cache)
                for dictionary in self.hatchery_dictionaries.values()
            ]

store = Store()
