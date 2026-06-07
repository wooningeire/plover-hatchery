import json
from collections.abc import Iterable
from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable, Protocol, final

from plover_hatchery.lib.trie.NondeterministicTrie import NondeterministicTrie


class CompilableHatcheryDictionary(Protocol):
    def compile(self, *, refresh_cache: bool=False) -> dict[str, Any]: ...
    def invalidate_lookup_cache(self) -> None: ...


@dataclass(frozen=True)
class HatcheryLookup:
    translations: list[str]
    breakdown_translation: Callable[[str], str | None]
    breakdown_lookup: Callable[[tuple[str, ...], list[str]], str | None]


@final
class Store:
    def __init__(self):
        self.breakdown_translation: Callable[[str], str | None] | None = None
        self.breakdown_lookup: Callable[[tuple[str, ...], list[str]], str | None] | None = None
        self.trie: NondeterministicTrie | None = None
        self.translations: list[str] | None = None
        self.hatchery_dictionaries: dict[str, CompilableHatcheryDictionary] = {}
        self.hatchery_lookups: dict[str, HatcheryLookup] = {}
        self.__hatchery_compile_lock = RLock()

    def register_hatchery_dictionary(self, path: str, dictionary: CompilableHatcheryDictionary):
        with self.__hatchery_compile_lock:
            self.hatchery_dictionaries[path] = dictionary

    def register_hatchery_lookup(
        self,
        path: str,
        *,
        translations: list[str],
        breakdown_translation: Callable[[str], str | None],
        breakdown_lookup: Callable[[tuple[str, ...], list[str]], str | None],
    ):
        with self.__hatchery_compile_lock:
            self.hatchery_lookups[path] = HatcheryLookup(
                translations=translations,
                breakdown_translation=breakdown_translation,
                breakdown_lookup=breakdown_lookup,
            )

    def invalidate_hatchery_lookup(self, path: str):
        with self.__hatchery_compile_lock:
            self.hatchery_lookups.pop(path, None)

    def compile_hatchery_dictionaries(self, *, refresh_cache: bool=False):
        with self.__hatchery_compile_lock:
            return [
                dictionary.compile(refresh_cache=refresh_cache)
                for dictionary in self.hatchery_dictionaries.values()
            ]

    def breakdown_hatchery_translation(self, translation: str):
        lookups = self.__compiled_hatchery_lookups()
        if len(lookups) == 0:
            return None

        return _join_json_array_results(
            lookup.breakdown_translation(translation)
            for lookup in lookups
        )

    def breakdown_hatchery_lookup(self, stroke_stenos: tuple[str, ...]):
        lookups = self.__compiled_hatchery_lookups()
        if len(lookups) == 0:
            return None

        return _join_json_array_results(
            lookup.breakdown_lookup(stroke_stenos, lookup.translations)
            for lookup in lookups
        )

    def __compiled_hatchery_lookups(self):
        with self.__hatchery_compile_lock:
            return tuple(self.hatchery_lookups.values())


def _join_json_array_results(results: Iterable[str | None]):
    joined: list[Any] = []
    has_result = False

    for result in results:
        if result is None:
            continue

        has_result = True
        try:
            parsed_result = json.loads(result)
        except json.JSONDecodeError:
            return result

        if not isinstance(parsed_result, list):
            return result

        joined.extend(parsed_result)

    if not has_result:
        return None

    return json.dumps(joined)


store = Store()
