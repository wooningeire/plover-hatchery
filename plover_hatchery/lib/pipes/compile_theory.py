from collections import defaultdict
from collections.abc import Iterable
from typing import cast, TypeVar, Generic, Any, Protocol, Callable, final
from dataclasses import dataclass

from plover.steno import Stroke

from plover_hatchery.lib.sopheme import Sopheme, SophemeSeq

from ..trie import  NondeterministicTrie
from .Hook import Hook
from .Plugin import Plugin
from .Theory import Theory, TheoryLookup


T = TypeVar("T")


@final
class TheoryHooks:
    class OnBuildLookup(Protocol):
        def __call__(self) -> Any: ...
    class AddEntry(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[str, int], sophemes: SophemeSeq, entry_id: int) -> None: ...
    class Lookup(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[str, int], stroke_stenos: tuple[str, ...], translations: list[str]) -> "str | None": ...
    class ReverseLookup(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[str, int], translation: str, reverse_translations: dict[str, list[int]]) -> Iterable[tuple[str, ...]]: ...
    

    build_lookup = Hook(OnBuildLookup)
    add_entry = Hook(AddEntry)
    lookup = Hook(Lookup)
    reverse_lookup = Hook(ReverseLookup)


def compile_theory(
    *plugins: Plugin[Any],
):
    hooks = TheoryHooks()

    plugins_map: dict[int, Any] = {}
    def get_plugin_api(plugin_factory: Callable[..., Plugin[T]]) -> T:
        plugin_id = id(plugin_factory)

        if plugin_id not in plugins_map:
            try:
                plugins_map[plugin_id] = plugin_factory().initialize(get_plugin_api=get_plugin_api, base_hooks=hooks)
            except TypeError:
                raise ValueError("Plugin is missing dependency that has required settings")
        
        return cast(T, plugins_map[plugin_id])


    for plugin in plugins:
        if plugin.id in plugins_map: raise ValueError("duplicate plugin")

        plugins_map[plugin.id] = plugin.initialize(get_plugin_api=get_plugin_api, base_hooks=hooks)


    def build_lookup(entries: Iterable[str]):
        states: dict[int, Any] = {}
        for plugin_id, handler in hooks.build_lookup.ids_handlers():
            states[plugin_id] = handler()


        trie: NondeterministicTrie[str, int] = NondeterministicTrie()

        n_entries = 0
        n_passed_parses = 0
        n_passed_additions = 0

        translations: list[str] = []
        reverse_translations: dict[str, list[int]] = defaultdict(lambda: [])

        for i, line in enumerate(entries):
            if i % 1000 == 0:
                print(f"hatched {i}")

            translations.append("")

            try:
                sophemes = tuple(Sopheme.parse_seq(line.strip()))
                n_passed_parses += 1

                try:
                    entry_id = len(translations) - 1

                    add_entry(states, trie, sophemes, entry_id)

                    translation = Sopheme.get_translation(sophemes)
                    translations[-1] = translation
                    reverse_translations[translation].append(entry_id)

                    n_passed_additions += 1
                except Exception as e:
                    # import traceback
                    # print(f"failed to add {line.strip()}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")
                    pass
            except Exception as e:
                # print(f"failed to parse {line.strip()}: {e}")
                pass

            n_entries += 1
        # while len(line := file.readline()) > 0:
        #     _add_entry(trie, Sopheme.parse_seq())

        n_failed_additions = n_entries - n_passed_additions
        n_failed_parses = n_entries - n_passed_parses

        print(f"""
Hatched {n_entries} entries
    {n_failed_additions} ({n_failed_additions / n_entries * 100:.2f}%) total failed additions
    ({n_failed_parses} ({n_failed_parses / n_entries * 100:.2f}%) failed parsing)
""")

        # print(trie)

        def true_lookup(stroke_stenos: tuple[str, ...]):
            return lookup(states, trie, stroke_stenos, translations)

        def true_reverse_lookup(translation: str):
            return reverse_lookup(states, trie, translation, reverse_translations)

        return TheoryLookup(true_lookup, true_reverse_lookup)
        

    def add_entry(states: dict[int, Any], trie: NondeterministicTrie[str, int], sophemes: Iterable[Sopheme], entry_id: int):
        for plugin_id, handler in hooks.add_entry.ids_handlers():
            handler(trie=trie, sophemes=SophemeSeq(tuple(sophemes)), entry_id=entry_id)


    def lookup(states: dict[int, Any], trie: NondeterministicTrie[str, int], stroke_stenos: tuple[str, ...], translations: list[str]) -> "str | None":
        for plugin_id, handler in hooks.lookup.ids_handlers():
            result = handler(trie=trie, stroke_stenos=stroke_stenos, translations=translations)
            if result is not None:
                return result
        
        return None


    def reverse_lookup(states: dict[int, Any], trie: NondeterministicTrie[str, int], translation: str, reverse_translations: dict[str, list[int]]) -> list[tuple[str, ...]]:
        results: list[tuple[str, ...]] = []

        for plugin_id, handler in hooks.reverse_lookup.ids_handlers():
            results.extend(handler(trie=trie, translation=translation, reverse_translations=reverse_translations))
        
        return results


    return Theory(
        build_lookup=build_lookup,
        # add_entry=add_entry,
        # lookup=lookup,
        # reverse_lookup=reverse_lookup,
    )

