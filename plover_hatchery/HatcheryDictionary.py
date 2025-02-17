from typing import Optional, Callable, Generator, Any

from plover.steno import Stroke
from plover.steno_dictionary import StenoDictionary
import plover.log

class HatcheryDictionary(StenoDictionary):
    readonly = True


    def __init__(self):
        super().__init__()

        """(override)"""
        self._longest_key = 12

        self.__maybe_lookup: "Callable[[tuple[str, ...]], str | None] | None" = None
        self.__maybe_reverse_lookup: "Callable[[str], list[tuple[str, ...]]] | None" = None

    def _load(self, filepath: str):
        from .lib.theory_presets.amphitheory import theory

        with open(filepath, "r", encoding="utf-8") as file:
            self.__maybe_lookup, self.__maybe_reverse_lookup = theory.build_lookup(entries=file)
            

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
        if self.__maybe_reverse_lookup is None: raise Exception("reverse lookup occurred before load")

        return self.__maybe_reverse_lookup(translation)
    
    def __lookup(self, stroke_stenos: tuple[str, ...]) -> Optional[str]:
        if self.__maybe_lookup is None: raise Exception("lookup occurred before load")

        return self.__maybe_lookup(stroke_stenos)

