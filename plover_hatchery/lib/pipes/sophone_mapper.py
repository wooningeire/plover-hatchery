from typing import Any, Generator, Iterable, Callable, TypeVar
from enum import Enum

from plover.steno import Stroke

from ..sopheme import Sound, Sopheme


T = TypeVar("T", bound=Enum)
K = TypeVar("K")
V = TypeVar("V")

def sophone_to_strokes_mapper(Sophone: T, get_sophone_from_sound: Callable[[Sound], T]):
    def map_sophones(mappings: "dict[str, str | Iterable[str]]") -> Callable[[Sound], Generator[Stroke, None, None]]:
        def map_steno_or_stenos(steno_or_stenos: "str | Iterable[str]"):
            if isinstance(steno_or_stenos, str):
                return (Stroke.from_steno(steno_or_stenos),)

            return tuple(Stroke.from_steno(steno) for steno in steno_or_stenos)
    

        chords = {
            Sophone.__dict__[key]: map_steno_or_stenos(steno_or_stenos)
            for key, steno_or_stenos in mappings.items()
        }


        def generate(sound: Sound) -> Generator[Stroke, None, None]:
            sophone = get_sophone_from_sound(sound)
            if sophone not in chords:
                return
            
            yield from chords[sophone]

        return generate

    return map_sophones

def sophone_to_sopheme_mapper(Sophone: T, get_sophone_from_sound: Callable[[Sound], T]):
    def map_sophones(mappings: dict[str, str]):
        def parse_sopheme(sopheme_str: str):
            return next(Sopheme.parse_seq(sopheme_str))


        chords = {
            Sophone.__dict__[key]: parse_sopheme(sopheme_str)
            for key, sopheme_str in mappings.items()
        }


        def generate(sound: Sound):
            sophone = get_sophone_from_sound(sound)
            if sophone not in chords:
                return None
            
            return chords[sophone]

        return generate

    return map_sophones

