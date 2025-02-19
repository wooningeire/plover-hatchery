from dataclasses import dataclass
from enum import Enum
from typing import Any, Generator, final, Callable
from collections.abc import Iterable, Generator

from plover.steno import Stroke

from plover_hatchery.lib.sopheme import Sound, Sopheme


@final
@dataclass(frozen=True)
class Sophone:
    name: str

    def __str__(self):
        return self.name


@final
class SophoneType:
    def __init__(self, sophones: dict[str, Sophone], from_sound_callback: "Callable[[Sound, SophoneType], Iterable[Sophone]]"):
        self.sophones = sophones
        self.__from_sound_callback = from_sound_callback


    def from_sound(self, sound: Sound):
        return self.__from_sound_callback(sound, self)


    @staticmethod
    def create_with_sophones(sophone_names: str, from_sound_mappings: "dict[str, str | Callable[[Sound], str]]"):
        return SophoneType(
            {
                name: Sophone(name)
                for name in sophone_names.split()
            },
            SophoneType.mapper_from_sounds(from_sound_mappings),
        )

    
    def __getitem__(self, name: str):
        return self.sophones[name]

    
    def iterate(self, sophone_names: str):
        for name in sophone_names.split():
            yield self.sophones[name]



    @staticmethod
    def mapper_from_sounds(mappings: "dict[str, str | Callable[[Sound], str]]"):
        def mapper(sound: Sound, sophone_type: SophoneType):
            result = mappings[sound.keysymbol.base_symbol]

            if isinstance(result, Callable):
                return sophone_type.iterate(result(sound))
            else:
                return sophone_type.iterate(result)

        return mapper

    def given_sound_maps_to_sophones(self, target_sophone_names: str):
        target_sophones = set(self.iterate(target_sophone_names))

        def check_sound(sound: Sound):
            for sophone in self.from_sound(sound):
                if sophone in target_sophones:
                    return True
            
            return False
        
        return check_sound

    class MapperToChords:
        def __init__(self, sophone_type: "SophoneType", chords: dict[Sophone, tuple[Stroke, ...]]):
            self.__sophone_type = sophone_type
            self.__chords = chords


        def __call__(self, sound: Sound) -> Generator[Stroke, None, None]:
            for sophone in self.__sophone_type.from_sound(sound):
                if sophone not in self.__chords: continue
                yield from self.__chords[sophone]


    def map_given_sound_to_chords_by_sophone(self, mappings: "dict[str, str | Iterable[str]]") -> Callable[[Sound], Generator[Stroke, None, None]]:
        def map_steno_or_stenos(steno_or_stenos: "str | Iterable[str]") -> tuple[Stroke, ...]:
            if isinstance(steno_or_stenos, str):
                return (Stroke.from_steno(steno_or_stenos),)

            return tuple(Stroke.from_steno(steno) for steno in steno_or_stenos)
    

        chords = {
            self[key]: map_steno_or_stenos(steno_or_stenos)
            for key, steno_or_stenos in mappings.items()
        }

        return SophoneType.MapperToChords(self, chords)


    def mapper_to_sophemes(self, mappings: dict[str, str]):
        def parse_sopheme(sopheme_str: str):
            return next(Sopheme.parse_seq(sopheme_str))


        chords = {
            self[key]: parse_sopheme(sopheme_str)
            for key, sopheme_str in mappings.items()
        }


        def generate(sound: Sound):
            for sophone in self.from_sound(sound):
                if sophone not in chords: continue
                yield chords[sophone]

        return generate


    def given_sound_is_pronounced_as(self, target_sophone_names: str):
        target_sophones = set(self.iterate(target_sophone_names))

        def check(sound: Sound):
            return any(sophone in target_sophones for sophone in self.from_sound(sound))

        return check