from dataclasses import dataclass
from enum import Enum, auto
from typing import cast, Any, Generator, final, Callable
from collections.abc import Iterable, Generator

from plover.steno import Stroke

from plover_hatchery.lib.sopheme import Sopheme, DefinitionCursor
from plover_hatchery.lib.sopheme.parse.parse_sopheme_sequence import parse_entry_definition, parse_sopheme_seq


@final
@dataclass(frozen=True)
class Sophone:
    name: str

    def __str__(self):
        return self.name


@final
class _MapResultType(Enum):
    Str = auto()
    Fn = auto()

_MapResultFn = Callable[[DefinitionCursor], str]

@final
@dataclass(frozen=True)
class _MapResult:
    type: _MapResultType
    value: "str | _MapResultFn"

    @staticmethod
    def of(value: "str | _MapResultFn"):
        if isinstance(value, Callable):
            return _MapResult(_MapResultType.Fn, value)
        
        return _MapResult(_MapResultType.Str, value)

    def resolve(self, phoneme: DefinitionCursor):
        if self.type is _MapResultType.Fn:
            value = cast(_MapResultFn, self.value)
            return value(phoneme)
        
        value = cast(str, self.value)
        return value



@final
class SophoneType:
    def __init__(self, sophones: dict[str, Sophone], from_sound_callback: "Callable[[DefinitionCursor, SophoneType], Iterable[Sophone]]"):
        self.sophones = sophones
        self.__from_sound_callback = from_sound_callback


    def from_phoneme(self, phoneme: DefinitionCursor):
        return self.__from_sound_callback(phoneme, self)


    @staticmethod
    def create_with_sophones(sophone_names: str, from_phoneme_mappings: "dict[str, str | Callable[[DefinitionCursor], str]]"):
        return SophoneType(
            {
                name: Sophone(name)
                for name in sophone_names.split()
            },
            SophoneType.mapper_from_phonemes(from_phoneme_mappings),
        )

    
    def __getitem__(self, name: str):
        return self.sophones[name]

    
    def iterate(self, sophone_names: str):
        for name in sophone_names.split():
            yield self.sophones[name]



    @staticmethod
    def mapper_from_phonemes(mappings: "dict[str, str | Callable[[DefinitionCursor], str]]"):
        new_mappings = {
            key: _MapResult.of(value)
            for key, value in mappings.items()
        }

        def mapper(phoneme: DefinitionCursor, sophone_type: SophoneType):
            result = new_mappings[phoneme.keysymbol.base_symbol]
            return sophone_type.iterate(result.resolve(phoneme))

        return mapper

    def given_phoneme_maps_to_sophones(self, target_sophone_names: str):
        target_sophones = set(self.iterate(target_sophone_names))

        def check_sound(sound: DefinitionCursor):
            for sophone in self.from_phoneme(sound):
                if sophone in target_sophones:
                    return True
            
            return False
        
        return check_sound

    class MapperToChords:
        def __init__(self, sophone_type: "SophoneType", chords: dict[Sophone, tuple[Stroke, ...]]):
            self.__sophone_type = sophone_type
            self.__chords = chords


        def __call__(self, phoneme: DefinitionCursor) -> Generator[Stroke, None, None]:
            for sophone in self.__sophone_type.from_phoneme(phoneme):
                if sophone not in self.__chords: continue
                yield from self.__chords[sophone]


    def map_given_phoneme_to_chords_by_sophone(self, mappings: "dict[str, str | Iterable[str]]") -> Callable[[DefinitionCursor], Generator[Stroke, None, None]]:
        def map_steno_or_stenos(steno_or_stenos: "str | Iterable[str]") -> tuple[Stroke, ...]:
            if isinstance(steno_or_stenos, str):
                return tuple(Stroke.from_steno(steno) for steno in steno_or_stenos.split())

            return tuple(Stroke.from_steno(steno) for steno in steno_or_stenos)
    

        chords = {
            self[key]: map_steno_or_stenos(steno_or_stenos)
            for key, steno_or_stenos in mappings.items()
        }

        return SophoneType.MapperToChords(self, chords)


    def mapper_to_sophemes(self, mappings: dict[str, str]):
        def parse_sopheme(sopheme_str: str):
            return next(parse_sopheme_seq(sopheme_str))


        chords = {
            self[key]: parse_sopheme(sopheme_str)
            for key, sopheme_str in mappings.items()
        }


        def generate(phoneme: DefinitionCursor):
            for sophone in self.from_phoneme(phoneme):
                if sophone not in chords: continue
                yield chords[sophone]

        return generate


    def given_sound_is_pronounced_as(self, target_sophone_names: str):
        target_sophones = set(self.iterate(target_sophone_names))

        def check(phoneme: DefinitionCursor):
            return any(sophone in target_sophones for sophone in self.from_phoneme(phoneme))

        return check