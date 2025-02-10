from typing import Any, Generator
from collections.abc import Iterable


from plover.steno import Stroke

from ..sopheme import Sound


def map_unstressed_vowels(chars_to_stenos: "dict[str, str | Iterable[str]]"):
    chars_to_strokes = {
        char: (Stroke.from_steno(steno_or_stenos),)
            if isinstance(steno_or_stenos, str)
            else (Stroke.from_steno(steno) for steno in steno_or_stenos)
        for char, steno_or_stenos in chars_to_stenos.items()
    }

    def generate(sound: Sound) -> Generator[Stroke, None, None]:
        if sound.keysymbol.stress == 1: return

        result = chars_to_strokes.get(sound.sopheme.chars)
        if result is None: return

        yield from result

    return generate