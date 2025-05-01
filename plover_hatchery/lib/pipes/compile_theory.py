from plover_hatchery.lib.sopheme.Sopheme import Sopheme


from collections import defaultdict
from collections.abc import Iterable
from typing import Generator, cast, TypeVar, Generic, Any, Protocol, Callable, final
from dataclasses import dataclass

from plover.steno import Stroke

from plover_hatchery.lib.sopheme import Sopheme, SophemeSeq, parse_entry_definition
from plover_hatchery.lib.sopheme.parse.parse_sopheme_sequence import Transclusion

from ..trie import  NondeterministicTrie
from .Hook import Hook
from .Plugin import Plugin
from .Theory import Theory, TheoryLookup


T = TypeVar("T")


@final
class TheoryHooks:
    class OnBuildLookup(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[str, int]) -> Any: ...
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


    def build_lookup(entry_lines: Iterable[tuple[str, str]]):
        trie: NondeterministicTrie[str, int] = NondeterministicTrie()


        states: dict[int, Any] = {}
        for plugin_id, handler in hooks.build_lookup.ids_handlers():
            states[plugin_id] = handler(trie=trie)


        n_entries = 0
        n_addable_entries = 0
        n_passed_parses = 0
        n_passed_additions = 0

        translations: list[str] = []
        reverse_translations: dict[str, list[int]] = defaultdict(lambda: [])


        entries: "dict[str, tuple[Transclusion | Sopheme, ...]]" = {}

        def resolve_sophemes(definition: "tuple[Transclusion | Sopheme, ...]", visited: set[str]) -> Generator[Sopheme, None, None]:
            for entity in definition:
                if isinstance(entity, Sopheme):
                    yield entity
                    continue
                    
                if entity.target_varname in visited:
                    raise Exception("Circular dependency")

                yield from resolve_sophemes(entries[entity.target_varname], visited | {entity.target_varname})

        for i, (varname, definition_str) in enumerate(entry_lines):
            if i % 1000 == 0:
                print(f"hatched {i}")

            try:
                entries[varname] = tuple(parse_entry_definition(definition_str.strip()))
                n_passed_parses += 1
            except Exception as e:
                # print(f"failed to parse {definition_str.strip()}: {e}")
                pass

            n_entries += 1
        # while len(line := file.readline()) > 0:
        #     _add_entry(trie, Sopheme.parse_seq())

        for i, (varname, definition) in enumerate(entries.items()):
            if i % 1000 == 0:
                print(f"checked/wrote {i}")

            if any(varname.startswith(modifier) for modifier in "@#^") or varname.endswith("^"):
                continue

            translations.append("")

            n_addable_entries += 1

            try:
                sophemes = tuple(resolve_sophemes(definition, {varname}))

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

        n_failed_additions = n_addable_entries - n_passed_additions
        n_failed_parses = n_entries - n_passed_parses

        print(f"""
Parsed {n_entries} entries
    ({n_failed_parses} ({n_failed_parses / n_entries * 100:.2f}%) failed)
Added {n_addable_entries} entries
    ({n_failed_additions} ({f"{n_failed_additions / n_addable_entries * 100:.2f}" if n_addable_entries > 0 else "nan"}%) failed)
""")

        # print(trie)

        def true_lookup(stroke_stenos: tuple[str, ...]):
            return lookup(states, trie, stroke_stenos, translations)

        def true_reverse_lookup(translation: str):
            return reverse_lookup(states, trie, translation, reverse_translations)

        # print(true_reverse_lookup("airworthiest"))

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

