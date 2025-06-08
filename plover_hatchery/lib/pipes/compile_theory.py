from plover_hatchery.lib.pipes.types import EntryIndex

from collections import defaultdict
from collections.abc import Iterable, Generator
from typing import cast, TypeVar, Any, Protocol, Callable, final

from plover_hatchery.lib.sopheme import parse_entry_definition

from plover_hatchery_lib_rs import Def, EntitySeq, DefView, DefDict
from .Hook import Hook
from .Plugin import Plugin
from .Theory import Theory, TheoryLookup


T = TypeVar("T")


@final
class TheoryHooks:
    class BeginBuildLookup(Protocol):
        def __call__(self) -> None: ...
    class CompleteBuildLookup(Protocol):
        def __call__(self) -> None: ...
    class ProcessDef(Protocol):
        def __call__(self, *, view: DefView) -> Def: ...
    class AddEntry(Protocol):
        def __call__(self, *, view: DefView, entry_id: EntryIndex) -> None: ...
    class Lookup(Protocol):
        def __call__(self, *, stroke_stenos: tuple[str, ...], translations: list[str]) -> "str | None": ...
    class ReverseLookup(Protocol):
        def __call__(self, *, translation: str, reverse_translations: dict[str, list[EntryIndex]]) -> Iterable[tuple[str, ...]]: ...
    

    begin_build_lookup = Hook(BeginBuildLookup)
    complete_build_lookup = Hook(CompleteBuildLookup)
    process_def = Hook(ProcessDef)
    add_entry = Hook(AddEntry)
    lookup = Hook(Lookup)
    reverse_lookup = Hook(ReverseLookup)


def compile_theory(
    plugin_generator: Callable[[], Generator[Plugin[Any], Any, None]],
):
    hooks = TheoryHooks()

    plugins_map: dict[int, Any] = {}
    def get_plugin_api(plugin_factory: Callable[..., Plugin[T]]) -> T:
        plugin_id = id(plugin_factory)

        if plugin_id not in plugins_map:
            try:
                plugins_map[plugin_id] = plugin_factory().initialize(get_plugin_api=get_plugin_api, base_hooks=hooks)
            except TypeError:
                raise ValueError(f"Plugin is missing dependency {plugin_factory.__name__} that has required settings")
        
        return cast(T, plugins_map[plugin_id])

    try:
        plugins = plugin_generator()
        plugin = next(plugins)
        while True:
            if plugin.id in plugins_map: raise ValueError("duplicate plugin")

            plugin_api = plugin.initialize(get_plugin_api=get_plugin_api, base_hooks=hooks)

            plugins_map[plugin.id] = plugin_api
            plugin = plugins.send(plugin_api)

    except StopIteration:
        pass


    def build_lookup(entry_lines: Iterable[tuple[str, str]]):
        states: dict[int, Any] = {}
        for plugin_id, handler in hooks.begin_build_lookup.ids_handlers():
            states[plugin_id] = handler()


        n_entries = 0
        n_addable_entries = 0
        n_passed_parses = 0
        n_passed_additions = 0

        translations: list[str] = []
        reverse_translations: dict[str, list[EntryIndex]] = defaultdict(lambda: [])



        defs = DefDict()

        for i, (varname, definition_str) in enumerate(entry_lines):
            if i % 1000 == 0:
                print(f"hatched {i}")

            try:
                defs.add(varname, EntitySeq(list(parse_entry_definition(definition_str.strip()))))
                n_passed_parses += 1
            except Exception as e:
                # import traceback
                # print(f"failed to parse {definition_str.strip()}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")
                pass

            n_entries += 1
        # while len(line := file.readline()) > 0:
        #     _add_entry(trie, Sopheme.parse_seq())

        i = 0

        @defs.foreach_key
        def _(varname: str):
            nonlocal i, n_addable_entries, n_passed_additions

            if i % 10000 == 0:
                print(f"checked/wrote {i}")

            i += 1

            if any(varname.startswith(modifier) for modifier in "@#") or "^" in varname:
                return

            translations.append("")

            n_addable_entries += 1

            try:
                entry_id = EntryIndex(len(translations) - 1)

                view = DefView(defs, defs.get_def(varname))

                add_entry(states, view, entry_id)

                translation = view.translation()
                translations[-1] = translation
                reverse_translations[translation].append(entry_id)

                n_passed_additions += 1
            except Exception as e:
                import traceback
                print(f"failed to add {varname}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")
                pass


        for plugin_id, handler in hooks.complete_build_lookup.ids_handlers():
            handler()
            

        n_failed_additions = n_addable_entries - n_passed_additions
        n_failed_parses = n_entries - n_passed_parses

        print(f"""
Parsed {n_entries} entries
    ({n_failed_parses} ({n_failed_parses / n_entries * 100:.2f}%) failed)
Added {n_addable_entries} entries
    ({n_failed_additions} ({f"{n_failed_additions / n_addable_entries * 100:.2f}" if n_addable_entries > 0 else "nan"}%) failed)
""")

        def true_lookup(stroke_stenos: tuple[str, ...]):
            return lookup(states, stroke_stenos, translations)

        def true_reverse_lookup(translation: str):
            return reverse_lookup(states, translation, reverse_translations)

        return TheoryLookup(true_lookup, true_reverse_lookup)
        

    def process_def(view: DefView):
        for plugin_id, handler in hooks.process_def.ids_handlers():
            view = DefView(view.defs, handler(view=view))
        return view


    def add_entry(states: dict[int, Any], view: DefView, entry_id: EntryIndex):
        new_view = process_def(view)

        for plugin_id, handler in hooks.add_entry.ids_handlers():
            handler(view=new_view, entry_id=entry_id)


    def lookup(states: dict[int, Any], stroke_stenos: tuple[str, ...], translations: list[str]) -> "str | None":
        for plugin_id, handler in hooks.lookup.ids_handlers():
            result = handler(stroke_stenos=stroke_stenos, translations=translations)
            if result is not None:
                return result
        
        return None


    def reverse_lookup(states: dict[int, Any], translation: str, reverse_translations: dict[str, list[EntryIndex]]) -> list[tuple[str, ...]]:
        results: list[tuple[str, ...]] = []

        for plugin_id, handler in hooks.reverse_lookup.ids_handlers():
            results.extend(handler(translation=translation, reverse_translations=reverse_translations))
        
        return results


    return Theory(
        build_lookup=build_lookup,
        # add_entry=add_entry,
        # lookup=lookup,
        # reverse_lookup=reverse_lookup,
    )

