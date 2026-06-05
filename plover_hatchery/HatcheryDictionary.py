from typing import Any, Callable, Optional
from threading import RLock

from plover.steno_dictionary import StenoDictionary

from .Store import store

class HatcheryDictionary(StenoDictionary):
    readonly = True


    def __init__(self):
        super().__init__()

        """(override)"""
        self._longest_key = 12

        self.__maybe_lookup: Callable[[tuple[str, ...]], str | None] | None = None
        self.__maybe_reverse_lookup: Callable[[str], list[tuple[str, ...]]] | None = None
        self.__filepath: str | None = None
        self.__compile_lock = RLock()

    def _load(self, filepath: str):
        self.__filepath = filepath
        self.__maybe_lookup = None
        self.__maybe_reverse_lookup = None
        store.register_hatchery_dictionary(filepath, self)
        self.compile()

    def compile(self, *, refresh_cache: bool=False) -> dict[str, Any]:
        with self.__compile_lock:
            if self.__filepath is None:
                raise RuntimeError("Hatchery dictionary compile requested before load")

            if (
                not refresh_cache
                and self.__maybe_lookup is not None
                and self.__maybe_reverse_lookup is not None
            ):
                return {
                    "path": self.__filepath,
                    "status": "already_compiled",
                }

            from .lib.dictionary.read import all_entries, read_hatchery_dictionary
            from .lib.theory_presets.amphitheory import theory

            def entry_lines():
                dictionary = read_hatchery_dictionary(self.__filepath)
                return all_entries(dictionary)

            lookup = theory.build_lookup(
                entry_lines=entry_lines,
                filename=self.__filepath,
                refresh_cache=refresh_cache,
            )

            self.__maybe_lookup = lookup.lookup
            self.__maybe_reverse_lookup = lookup.reverse_lookup

            store.breakdown_translation = lookup.breakdown_translation
            store.breakdown_lookup = lookup.breakdown_lookup

            return {
                "path": self.__filepath,
                "status": "refreshed_cache" if refresh_cache else "compiled",
            }
            

    def __getitem__(self, stroke_stenos: tuple[str, ...]) -> str:
        result = self.__lookup(stroke_stenos)
        if result is None:
            raise KeyError
        
        return result

    def get(self, stroke_stenos: tuple[str, ...], fallback=None) -> Optional[str]:
        result = self.__lookup(stroke_stenos)
        if result is None:
            return fallback
        
        return result
    
    def reverse_lookup(self, translation: str) -> list[tuple[str, ...]]:
        self.__ensure_compiled()

        return self.__maybe_reverse_lookup(translation)
    
    def __lookup(self, stroke_stenos: tuple[str, ...]) -> Optional[str]:
        self.__ensure_compiled()

        return self.__maybe_lookup(stroke_stenos)

    def __ensure_compiled(self):
        if self.__maybe_lookup is None or self.__maybe_reverse_lookup is None:
            self.compile()

