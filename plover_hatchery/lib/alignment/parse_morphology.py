from abc import ABC
from dataclasses import dataclass, field
from typing import NamedTuple, Union, final


class MorphemeSeq:
    def __init__(self):
        self.morphemes: "list[Morpheme]" = []

    def append(self, morpheme: "Morpheme"):
        self.morphemes.append(morpheme)

    @property
    def name(self):
        return "".join(morpheme.name for morpheme in self.morphemes)

    @property
    def phono(self):
        return " ".join(morpheme.phono for morpheme in self.morphemes)

    @property
    def ortho(self):
        return "".join(morpheme.ortho for morpheme in self.morphemes)


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
    morpheme_seq: MorphemeSeq = field(default_factory=MorphemeSeq)

    @property
    def dict_key(self):
        return AffixKey(self.is_suffix, self.morpheme_seq.name, self.morpheme_seq.phono, self.morpheme_seq.ortho)

    @property
    def varname(self):
        if self.is_suffix:
            return f"^{self.morpheme_seq.name}"
        
        return f"{self.morpheme_seq.name}^"


@final
class RootKey(NamedTuple):
    name: str
    phono: str
    ortho: str

@final
@dataclass(frozen=True)
class Root:
    morpheme_seq: MorphemeSeq = field(default_factory=MorphemeSeq)

    @property
    def dict_key(self):
        return RootKey(self.morpheme_seq.name, self.morpheme_seq.phono, self.morpheme_seq.ortho)

    @property
    def varname(self):
        return f"#{self.morpheme_seq.name}"

@final
class MorphemeKey(NamedTuple):
    name: str
    phono: str
    ortho: str

@final
@dataclass(frozen=True)
class Morpheme:
    parent: "Root | Affix"
    name: str
    phono: str
    ortho: str = ""

    @property
    def dict_key(self):
        return MorphemeKey(self.name, self.phono, self.ortho)

    @property
    def varname(self):
        return f"@{self.name}"

@final
@dataclass(frozen=True)
class Formatting:
    name: str
    ortho: str = ""


MorphologyPart = Union[Formatting, Morpheme]
MorphologyChunk = Union[Formatting, Root, Affix]


@final
@dataclass(frozen=True)
class Morphology:
    parts: tuple[MorphologyPart, ...]
    chunks: tuple[MorphologyChunk, ...]


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
        morphemes: list[MorphologyPart] = []
        chunks: list[MorphologyChunk] = []

        while self.morphology_index < len(self.morphology):
            if self.morphology_char in "{<>":
                morphemes.extend(self.__check_formatting())

                if self.morphology_char == "{":
                    self.__catch_up_transcription_index("{")
                    root = self.__consume_root()
                    morphemes.extend(root.morpheme_seq.morphemes)
                    chunks.append(root)

                elif self.morphology_char == ">":
                    self.__catch_up_transcription_index(">")
                    suffix = self.__consume_suffix()
                    morphemes.extend(suffix.morpheme_seq.morphemes)
                    chunks.append(suffix)

                elif self.morphology_char == "<":
                    self.__catch_up_transcription_index("<")
                    prefix = self.__consume_prefix()
                    morphemes.extend(prefix.morpheme_seq.morphemes)
                    chunks.append(prefix)

                self.morphology_index_at_last_part = self.morphology_index
                continue
            
            self.morphology_index += 1

        return Morphology(tuple(morphemes), tuple(chunks))

    
    def __catch_up_transcription_index(self, target_chars: str):
        while self.transcription_char not in target_chars:
            self.transcription_index += 1


    def __check_formatting(self):
        if self.morphology_index_at_last_part > self.morphology_index:
            yield Formatting(self.morphology_since_last_part) 


    def __consume_suffix(self):
        self.transcription_index += 1
        self.morphology_index += 1

        suffix = Affix(True)
        while True:
            if self.morphology_char == ">":
                self.morphology_index += 1
                break

            suffix.morpheme_seq.append(self.__consume_morpheme(suffix))

        return suffix


    def __consume_prefix(self):
        self.transcription_index += 1
        self.morphology_index += 1

        prefix = Affix(False)
        while True:
            if self.morphology_char == "<":
                self.morphology_index += 1
                break

            prefix.morpheme_seq.append(self.__consume_morpheme(prefix))

        return prefix


    def __consume_root(self):
        self.transcription_index += 1
        self.morphology_index += 1
        
        root = Root()
        while True:
            if self.morphology_char == "}":
                self.morphology_index += 1
                break

            root.morpheme_seq.append(self.__consume_morpheme(root))

        return root


    def __consume_morpheme(self, parent: "Root | Affix"):
        phono = ""
        while True:
            if self.transcription_char == "=":
                self.__catch_up_transcription_index(" $")
                self.transcription_index += 1
                break
                
            if self.transcription_char in "}<>":
                break

            phono += self.transcription_char
            self.transcription_index += 1

        name = ""
        while True:
            if self.morphology_char == "=":
                self.morphology_index += 2
                break
                
            if self.morphology_char in "}<>":
                break

            name += self.morphology_char
            self.morphology_index += 1

        return Morpheme(parent, name, phono.strip())


def split_morphology(transcription: str, morphology: str):
    return _Parser(transcription, morphology).split_morphology()
