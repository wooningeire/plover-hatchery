import timeit

from collections import defaultdict
from collections.abc import Iterable, Generator
from dataclasses import dataclass
from typing import cast, TypeVar, Any, Protocol, Callable, final

from plover_hatchery.lib.sopheme import parse_entry_definition

from plover_hatchery_lib_rs import Def, DefView, DefDict, Entity, TheorySymbol

from .Hook import Hook
from .Plugin import Plugin
from .Theory import Theory, TheoryLookup
from .compile_theory_io import CacheLoadResult, CompiledLookupCache


T = TypeVar("T")

ENTRY_FORMAT_SOPHEMES = "sophemes"
ENTRY_FORMAT_THEORY_SYMBOLS = "theory-symbols"


@dataclass(frozen=True)
class TheoryInputEntry:
    varname: str
    definition: str
    format: str = ENTRY_FORMAT_SOPHEMES
    translation: str | None = None


def _default_entry_translation(varname: str):
    return varname.split(":", 1)[0]


def _normalize_theory_input_entry(entry_line: Any):
    if isinstance(entry_line, TheoryInputEntry):
        return entry_line

    if all(hasattr(entry_line, attr) for attr in ("key", "definition", "format")):
        key = getattr(entry_line, "key")
        definition = getattr(entry_line, "definition")
        entry_format = getattr(entry_line, "format")
        translation = getattr(entry_line, "translation", None)

        if not isinstance(key, str):
            raise ValueError("entry key must be a string")
        if not isinstance(definition, str):
            raise ValueError("entry definition must be a string")
        if not isinstance(entry_format, str):
            raise ValueError("entry format must be a string")
        if translation is not None and not isinstance(translation, str):
            raise ValueError("entry translation must be a string")

        return TheoryInputEntry(
            varname=key,
            definition=definition,
            format=entry_format,
            translation=translation,
        )

    if isinstance(entry_line, (tuple, list)) and len(entry_line) in {2, 3}:
        varname, definition = entry_line[:2]
        entry_format = entry_line[2] if len(entry_line) == 3 else ENTRY_FORMAT_SOPHEMES

        if not isinstance(varname, str):
            raise ValueError("entry key must be a string")
        if not isinstance(definition, str):
            raise ValueError("entry definition must be a string")
        if not isinstance(entry_format, str):
            raise ValueError("entry format must be a string")

        return TheoryInputEntry(
            varname=varname,
            definition=definition,
            format=entry_format,
        )

    raise ValueError("entry line must be an entry object or a 2/3-item sequence")


@final
class TheoryHooks:
    class BeginBuildLookup(Protocol):
        def __call__(self) -> None: ...
    class CompleteBuildLookup(Protocol):
        def __call__(self) -> None: ...
    class ProcessDef(Protocol):
        def __call__(self, *, view: DefView) -> Def: ...
    class AddEntry(Protocol):
        def __call__(self, *, view: DefView, entry_id: int) -> None: ...
    class AddTheorySymbolsEntry(Protocol):
        def __call__(self, *, theory_symbols: tuple[TheorySymbol, ...], entry_id: int) -> None: ...
    class Lookup(Protocol):
        def __call__(self, *, stroke_stenos: tuple[str, ...], translations: list[str]) -> str | None: ...
    class ReverseLookup(Protocol):
        def __call__(self, *, translation: str, reverse_translations: dict[str, list[int]]) -> Iterable[tuple[str, ...]]: ...
    class BreakdownTranslation(Protocol):
        def __call__(self, *, translation: str, entries: list[str], reverse_translations: dict[str, list[int]]) -> str | None: ...
    class BreakdownLookup(Protocol):
        def __call__(self, *, stroke_stenos: tuple[str, ...], translations: list[str]) -> str | None: ...
    class ExportBuildCache(Protocol):
        def __call__(self, *, state: Any) -> tuple[str, Any] | None: ...
    class ImportBuildCache(Protocol):
        def __call__(self, *, state: Any, cache: dict[str, Any]) -> None: ...

    begin_build_lookup = Hook(BeginBuildLookup)
    complete_build_lookup = Hook(CompleteBuildLookup)
    process_def = Hook(ProcessDef)
    add_entry = Hook(AddEntry)
    add_theory_symbols_entry = Hook(AddTheorySymbolsEntry)
    lookup = Hook(Lookup)
    reverse_lookup = Hook(ReverseLookup)
    breakdown_translation = Hook(BreakdownTranslation)
    breakdown_lookup = Hook(BreakdownLookup)
    export_build_cache = Hook(ExportBuildCache)
    import_build_cache = Hook(ImportBuildCache)


def compile_theory(
    plugin_generator: Callable[[], Generator[Plugin[Any], Any, None]],
):
    def build_lookup(
        entry_lines: Iterable[Any] | Callable[[], Iterable[Any]],
        filename: str="",
        refresh_cache: bool=False,
    ):
        return _compile_theory_lookup_builder(plugin_generator).build_lookup(
            entry_lines=entry_lines,
            filename=filename,
            refresh_cache=refresh_cache,
        )

    return Theory(build_lookup=build_lookup)


def _compile_theory_lookup_builder(
    plugin_generator: Callable[[], Generator[Plugin[Any], Any, None]],
):
    from plover_hatchery.Store import store


    hooks = TheoryHooks()

    plugins_map: dict[int, Any] = {}
    def get_plugin_api(plugin_factory: Callable[..., Plugin[T]]) -> T:
        plugin_id = id(plugin_factory)

        if plugin_id not in plugins_map:
            raise ValueError(f"Plugin is missing dependency {plugin_factory.__name__}")
            # try:
            #     plugins_map[plugin_id] = plugin_factory().initialize(get_plugin_api=get_plugin_api, base_hooks=hooks)
            # except TypeError:
            #     raise ValueError(f"Plugin is missing dependency {plugin_factory.__name__} that has required settings")
        
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




    translations: list[str] = []
    defs_list: list[str] = []
    reverse_translations: dict[str, list[int]] = defaultdict(lambda: [])

    store.translations = translations

    def build_lookup(
        entry_lines: Iterable[Any] | Callable[[], Iterable[Any]],
        filename: str="",
        refresh_cache: bool=False,
    ):
        def create_states():
            states: dict[int, Any] = {}
            for plugin_id, handler in hooks.begin_build_lookup.ids_handlers():
                states[plugin_id] = handler()
            return states

        def resolve_entry_lines():
            return entry_lines() if callable(entry_lines) else entry_lines


        n_entries = 0
        n_addable_entries = 0
        n_passed_parses = 0
        n_passed_additions = 0

        cache = CompiledLookupCache(filename=filename, translations=translations)

        def try_load_cache(states: dict[int, Any]):
            try:
                return cache.load(
                    hooks=hooks,
                    states=states,
                    translations=translations,
                    reverse_translations=reverse_translations,
                    defs_list=defs_list,
                )
            except Exception as e:
                print(f"\x1b[33mIgnoring compiled trie cache {cache.path}: {e}\x1b[0m")
                return CacheLoadResult(False)

        def save_cache(label: str):
            try:
                cache.save(
                    hooks=hooks,
                    states=states,
                    translations=translations,
                    reverse_translations=reverse_translations,
                    defs_list=defs_list,
                )
                if cache.path is not None:
                    print(f"\x1b[32m{label} compiled trie cache {cache.path}\x1b[0m")
            except Exception as e:
                print(f"\x1b[33mCould not save compiled trie cache {cache.path}: {e}\x1b[0m")

        print(f"\x1b[1;36mHatching {filename}...\x1b[0m")

        states = create_states()
        cache_load_result = CacheLoadResult(False)
        loaded_from_cache = False
        if cache.can_load_before_entries:
            cache_load_result = try_load_cache(states)
            loaded_from_cache = bool(cache_load_result)
            if loaded_from_cache:
                n_addable_entries = len(translations) - cache.base_entry_id
                n_passed_additions = n_addable_entries
                print(f"\x1b[32mLoaded compiled trie cache {cache.path}\x1b[0m")

        defs = DefDict()
        addable_entries: list[TheoryInputEntry] = []
        direct_theory_symbols: dict[str, tuple[TheorySymbol, ...]] = {}

        def populate_dict():
            nonlocal n_entries, n_passed_parses

            for i, raw_entry_line in enumerate(resolve_entry_lines()):
                if i % 10000 == 0:
                    print(f"\x1b[FParsed {i} entries")

                try:
                    entry = _normalize_theory_input_entry(raw_entry_line)
                except ValueError:
                    n_entries += 1
                    continue

                cache.update_source(
                    entry.varname,
                    entry.definition,
                    entry_format=entry.format,
                    translation=entry.translation,
                )

                try:
                    if entry.format == ENTRY_FORMAT_SOPHEMES:
                        defs.add(
                            entry.varname,
                            list(parse_entry_definition(entry.definition.strip())),
                        )
                    elif entry.format == ENTRY_FORMAT_THEORY_SYMBOLS:
                        direct_theory_symbols[entry.varname] = TheorySymbol.parse_seq(
                            entry.definition.strip()
                        )
                    else:
                        raise ValueError(f"unsupported entry format {entry.format}")

                    addable_entries.append(entry)
                    n_passed_parses += 1
                except ValueError as e:
                    # import traceback
                    # print(f"failed to parse {entry.definition.strip()}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")
                    pass

                n_entries += 1

        if not loaded_from_cache:
            print("\x1b[35m")
            duration = timeit.timeit(populate_dict, number=1)
            n_failed_parses = n_entries - n_passed_parses
            print(f""""\x1b[FParsed {n_entries} entries
    \x1b[31m{n_failed_parses} ({n_failed_parses / n_entries * 100:.2f}%) failed
    \x1b[32mTook {duration} s""")

            states = create_states()
            if not cache.can_load_before_entries:
                cache_load_result = try_load_cache(states)
                loaded_from_cache = bool(cache_load_result)
                if loaded_from_cache:
                    n_addable_entries = len(translations) - cache.base_entry_id
                    n_passed_additions = n_addable_entries
                    print(f"\x1b[32mLoaded compiled trie cache {cache.path}\x1b[0m")

        def add_entries():
            nonlocal n_addable_entries, n_passed_additions

            for i, entry in enumerate(addable_entries):
                varname = entry.varname
                if any(varname.startswith(modifier) for modifier in "@#") or "^" in varname:
                    continue

                if i % 1000 == 0:
                    print(f"\x1b[FAdded {i} entries")

                translations.append("")
                defs_list.append("")

                n_addable_entries += 1

                try:
                    entry_id = len(translations) - 1

                    if entry.format == ENTRY_FORMAT_THEORY_SYMBOLS:
                        add_theory_symbols_entry(
                            states,
                            direct_theory_symbols[varname],
                            entry_id,
                        )
                        translation = entry.translation or _default_entry_translation(varname)
                        defs_list[-1] = f"{varname} = {entry.definition}"
                    else:
                        def_item = defs.get_def(varname)
                        view = DefView(defs, def_item)

                        add_entry(states, view, entry_id)

                        translation = view.translation()
                        defs_list[-1] = str(def_item)

                    translations[-1] = translation
                    reverse_translations[translation].append(entry_id)

                    n_passed_additions += 1
                except Exception as e:
                    import traceback
                    # print(f"failed to add {varname}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")
                    pass


        if not loaded_from_cache:
            print("\x1b[35m")
            duration = timeit.timeit(add_entries, number=1)
            n_failed_additions = n_addable_entries - n_passed_additions
            print(f""""\x1b[FAdded {n_addable_entries} entries
    \x1b[31m{n_failed_additions} ({f"{n_failed_additions / n_addable_entries * 100:.2f}" if n_addable_entries > 0 else "nan"}%) failed
    \x1b[32mTook {duration} s""")

            save_cache("Saved")
        elif refresh_cache and cache_load_result.needs_refresh:
            save_cache("Refreshed")

        print("\x1b[0m")

        for plugin_id, handler in hooks.complete_build_lookup.ids_handlers():
            handler()
            

        def true_lookup(stroke_stenos: tuple[str, ...]):
            return lookup(states, stroke_stenos, translations)

        def true_reverse_lookup(translation: str):
            return reverse_lookup(states, translation, reverse_translations)

        def true_breakdown_translation(translation: str):
            return breakdown_translation(states, translation, defs_list, reverse_translations)

        def true_breakdown_lookup(stroke_stenos: tuple[str, ...], translations: list[str]):
            return breakdown_lookup(states, stroke_stenos, translations)

        return TheoryLookup(
            true_lookup,
            true_reverse_lookup,
            true_breakdown_translation,
            true_breakdown_lookup,
            translations,
        )
        

    def process_def(view: DefView):
        for plugin_id, handler in hooks.process_def.ids_handlers():
            view = DefView(view.defs, handler(view=view))
        return view


    def add_entry(states: dict[int, Any], view: DefView, entry_id: int):
        new_view = process_def(view)

        for plugin_id, handler in hooks.add_entry.ids_handlers():
            handler(view=new_view, entry_id=entry_id)


    def add_theory_symbols_entry(
        states: dict[int, Any],
        theory_symbols: tuple[TheorySymbol, ...],
        entry_id: int,
    ):
        for plugin_id, handler in hooks.add_theory_symbols_entry.ids_handlers():
            handler(theory_symbols=theory_symbols, entry_id=entry_id)


    def lookup(states: dict[int, Any], stroke_stenos: tuple[str, ...], translations: list[str]) -> str | None:
        for plugin_id, handler in hooks.lookup.ids_handlers():
            result = handler(stroke_stenos=stroke_stenos, translations=translations)
            if result is not None:
                return result
        
        return None


    def reverse_lookup(states: dict[int, Any], translation: str, reverse_translations: dict[str, list[int]]) -> list[tuple[str, ...]]:
        results: list[tuple[str, ...]] = []

        for plugin_id, handler in hooks.reverse_lookup.ids_handlers():
            results.extend(handler(translation=translation, reverse_translations=reverse_translations))
        
        return results


    def breakdown_translation(states: dict[int, Any], translation: str, entries: list[str], reverse_translations: dict[str, list[int]]) -> str | None:
        for plugin_id, handler in hooks.breakdown_translation.ids_handlers():
            result = handler(translation=translation, entries=entries, reverse_translations=reverse_translations)
            if result is not None:
                return result
        
        return None

    def breakdown_lookup(states: dict[int, Any], stroke_stenos: tuple[str, ...], translations: list[str]) -> str | None:
        for plugin_id, handler in hooks.breakdown_lookup.ids_handlers():
            result = handler(stroke_stenos=stroke_stenos, translations=translations)
            if result is not None:
                return result
        
        return None


    return Theory(
        build_lookup=build_lookup,
        # add_entry=add_entry,
        # lookup=lookup,
        # reverse_lookup=reverse_lookup,
    )
