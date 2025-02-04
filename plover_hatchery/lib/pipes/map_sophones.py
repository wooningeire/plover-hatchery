from typing import Iterable

from plover.steno import Stroke

from ..sopheme import Sound
from ..sophone.Sophone import Sophone
from ..theory_defaults.amphitheory import amphitheory


def map_sophones(mappings: "dict[str, str | Iterable[str]]"):
    chords = {
        Sophone.__dict__[key]: (Stroke.from_steno(steno_or_stenos),)
            if isinstance(steno_or_stenos, str) else
            tuple(Stroke.from_steno(steno) for steno in steno_or_stenos)
        for key, steno_or_stenos in mappings.items()
    }

    def generate(sound: Sound):
        sophone = amphitheory.sound_sophone(sound)
        if sophone not in chords:
            return
        
        yield from chords[sophone]

    return generate
