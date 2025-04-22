from dataclasses import dataclass
from typing import NamedTuple, Union, final


@final
class AffixKey(NamedTuple):
    is_suffix: bool
    name: str
    phono: str
    ortho: str

@final
@dataclass(frozen=True)
class Affix:
    is_suffix: bool
    name: str
    phono: str
    ortho: str = ""

    def as_dict_key(self):
        return AffixKey(self.is_suffix, self.name, self.phono, self.ortho)

    @property
    def varname(self):
        if self.is_suffix:
            return f"^{self.name}"
        
        return f"{self.name}^"


@final
@dataclass(frozen=True)
class BoundMorpheme:
    name: str
    phono: str

@final
@dataclass(frozen=True)
class FreeMorpheme:
    parts: tuple[BoundMorpheme, ...]
    ortho: str = ""

@final
@dataclass(frozen=True)
class Formatting:
    name: str
    ortho: str = ""


MorphologyPart = Union[Formatting, FreeMorpheme, Affix]


@final
@dataclass
class _Parser:
    transcription: str
    morphology: str
    transcription_index: int = 0
    morphology_index: int = 0
    morphology_index_at_last_part: int = 0

    @property
    def transcription_char(self):
        return self.transcription[self.transcription_index]

    @property
    def morphology_char(self):
        return self.morphology[self.morphology_index]

    @property
    def morphology_since_last_part(self):
        return self.morphology[self.morphology_index_at_last_part:self.morphology_index]


    def split_morphology(self):
        parts: list[MorphologyPart] = []

        while self.morphology_index < len(self.morphology):
            if self.morphology_char == "{":
                parts.extend(self.__check_formatting())

                self.__catch_up_transcription_index("{")
                parts.append(self.__consume_free_morpheme())

                self.morphology_index_at_last_part = self.morphology_index
                continue

            if self.morphology_char == ">":
                parts.extend(self.__check_formatting())
                
                self.__catch_up_transcription_index(">")
                parts.append(self.__consume_suffix())
                
                self.morphology_index_at_last_part = self.morphology_index
                continue

            if self.morphology_char == "<":
                parts.extend(self.__check_formatting())
                
                self.__catch_up_transcription_index("<")
                parts.append(self.__consume_prefix())

                self.morphology_index_at_last_part = self.morphology_index
                continue
            
            self.morphology_index += 1

        return tuple(parts)

    
    def __catch_up_transcription_index(self, target_chars: str):
        while self.transcription_char not in target_chars:
            self.transcription_index += 1


    def __check_formatting(self):
        if self.morphology_index_at_last_part > self.morphology_index:
            yield Formatting(self.morphology_since_last_part) 


    def __consume_suffix(self):
        self.transcription_index += 1
        self.morphology_index += 1
    
        phono = ""
        while True:
            if self.transcription_char == ">":
                self.transcription_index += 1
                break

            phono += self.transcription_char
            self.transcription_index += 1

        name = ""
        while True:
            if self.morphology_char == ">":
                self.morphology_index += 1
                break

            name += self.morphology_char
            self.morphology_index += 1
        
        return Affix(True, name, phono.strip())


    def __consume_prefix(self):
        self.transcription_index += 1
        self.morphology_index += 1
    
        phono = ""
        while True:
            if self.transcription_char == "<":
                self.transcription_index += 1
                break

            phono += self.transcription_char
            self.transcription_index += 1

        name = ""
        while True:
            if self.morphology_char == "<":
                self.morphology_index += 1
                break

            name += self.morphology_char
            self.morphology_index += 1
        
        return Affix(False, name, phono.strip())


    def __consume_free_morpheme(self):
        self.transcription_index += 1
        self.morphology_index += 1
        
        parts: list[BoundMorpheme] = []
        while True:
            if self.morphology_char == "}":
                self.morphology_index += 1
                break

            parts.append(self.__consume_bound_morpheme())

        return FreeMorpheme(tuple(parts))


    def __consume_bound_morpheme(self):
        phono = ""
        while True:
            if self.transcription_char == "=":
                self.__catch_up_transcription_index(" $")
                self.transcription_index += 1
                break
                
            if self.transcription_char == "}":
                break

            phono += self.transcription_char
            self.transcription_index += 1

        name = ""
        while True:
            if self.morphology_char == "=":
                self.morphology_index += 2
                break
                
            if self.morphology_char == "}":
                break

            name += self.morphology_char
            self.morphology_index += 1

        return BoundMorpheme(name, phono.strip())


def split_morphology(transcription: str, morphology: str):
    return _Parser(transcription, morphology).split_morphology()
