from typing import Any, Generator


from plover.steno import Stroke

from ..sopheme import Sound


def map_unstressed_vowels(chars_to_stenos: dict[str, str]):
    chars_to_strokes = {
        char: Stroke.from_steno(steno)
        for char, steno in chars_to_stenos.items()
    }

    def generate(sound: Sound) -> Generator[Stroke, None, None]:
        if sound.keysymbol.stress == 1: return

        result = chars_to_strokes.get(sound.sopheme.chars)
        if result is None: return

        yield result

    return generate