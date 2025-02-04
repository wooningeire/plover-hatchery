from typing import Iterable, Callable, TypeVar
from enum import Enum

from plover.steno import Stroke

from ..sopheme import Sound


T = TypeVar("T", bound=Enum)

def sophone_mapper(Sophone: T, get_sophone_from_sound: Callable[[Sound], T]):
    def map_sophones(mappings: "dict[str, str | Iterable[str]]"):
        chords = {
            Sophone.__dict__[key]: (Stroke.from_steno(steno_or_stenos),)
                if isinstance(steno_or_stenos, str) else
                tuple(Stroke.from_steno(steno) for steno in steno_or_stenos)
            for key, steno_or_stenos in mappings.items()
        }

        def generate(sound: Sound):
            sophone = get_sophone_from_sound(sound)
            if sophone not in chords:
                return
            
            yield from chords[sophone]

        return generate

    return map_sophones
