from collections.abc import Iterable
from typing import cast, TypeVar, Any, Protocol, Callable, final

from plover.steno import Stroke

from plover_hatchery.lib.sopheme import Sopheme
from plover_hatchery.lib.trie import TrieIndex

from ..trie import  NondeterministicTrie
from ..sopheme import Sound
from .state import OutlineSounds
from .Hook import Hook
from .Plugin import Plugin
from .Theory import Theory


T = TypeVar("T")


@final
class TheoryHooks:
    class OnAddEntry(Protocol):
        def __call__(self, *, tries: TrieIndex, sophemes: Iterable[Sopheme], translation: str) -> None: ...
    class OnLookup(Protocol):
        def __call__(self, *, tries: TrieIndex, stroke_stenos: tuple[str, ...]) -> "str | None": ...
    class OnReverseLookup(Protocol):
        def __call__(self, *, tries: TrieIndex, translation: str) -> Iterable[tuple[str, ...]]: ...

    add_entry = Hook(OnAddEntry)
    lookup = Hook(OnLookup)
    reverse_lookup = Hook(OnReverseLookup)


def compile_theory(
    *plugins: Plugin[Any],
):
    hooks = TheoryHooks()

    plugins_map: dict[int, Any] = {}
    def get_plugin_api(plugin_factory: Callable[..., Plugin[T]]) -> T:
        plugin_id = id(plugin_factory)

        if plugin_id not in plugins_map:
            raise ValueError("plugin not found")
        
        return cast(T, plugins_map[plugin_id])


    for plugin in plugins:
        if plugin.id in plugins_map: raise ValueError("duplicate plugin")

        plugins_map[plugin.id] = plugin.initialize(get_plugin_api=get_plugin_api, base_hooks=hooks)



    def add_entry(tries: TrieIndex, sophemes: Iterable[Sopheme], translation: str):
        for handler in hooks.add_entry.handlers():
            handler(tries=tries, sophemes=sophemes, translation=translation)


    def lookup(tries: TrieIndex, stroke_stenos: tuple[str, ...]) -> "str | None":
        for handler in hooks.lookup.handlers():
            result = handler(tries=tries, stroke_stenos=stroke_stenos)
            if result is not None:
                return result
        
        return None


    def reverse_lookup(tries: TrieIndex, translation: str) -> list[tuple[str, ...]]:
        results: list[tuple[str, ...]] = []

        for handler in hooks.reverse_lookup.handlers():
            results.extend(handler(tries=tries, translation=translation))
        
        return results


    return Theory(
        add_entry=add_entry,
        lookup=lookup,
        reverse_lookup=reverse_lookup,
    )

