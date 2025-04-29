from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Generator, NamedTuple, Union, final

from plover_hatchery.lib.sopheme import Keysymbol


@final
class MorphemeSeq:
    def __init__(self):
        self.parts: "list[Morpheme | Formatting]" = []

    def append(self, morpheme: "Morpheme | Formatting"):
        self.parts.append(morpheme)

    def extend(self, morphemes: "Iterable[Morpheme | Formatting]"):
        self.parts.extend(morphemes)

    @property
    def name(self):
        return "".join(morpheme.name for morpheme in self.parts)

    @property
    def phono(self):
        return " ".join(morpheme.phono for morpheme in self.parts)

    @property
    def ortho(self):
        return "".join(morpheme.ortho for morpheme in self.parts)

    def repr(self, depth: int=0):
        return (
            "MorphemeSeq(\n"
            + "".join("  " * (depth + 1) + repr(morpheme) + "\n" for morpheme in self.parts)
            + ")"
        )

    def __repr__(self):
        return self.repr()


@final
class AffixStressNormalizedKey(NamedTuple):
    is_suffix: bool
    name: str
    morpheme_normalized_key: "tuple[MorphemeStressNormalizedKey, ...]"
    max_stress: int
    ortho: str

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
    def is_prefix(self):
        return not self.is_suffix

    @property
    def dict_key(self):
        return AffixKey(self.is_suffix, self.morpheme_seq.name, self.morpheme_seq.phono, self.morpheme_seq.ortho)

    @property
    def varname(self):
        if self.is_suffix:
            return f"^{self.morpheme_seq.name}"
        
        return f"{self.morpheme_seq.name}^"

    def parts(self):
        yield from self.morpheme_seq.parts

@final
class RootStressNormalizedKey(NamedTuple):
    name: str
    morpheme_normalized_key: "tuple[MorphemeStressNormalizedKey, ...]"
    max_stress: int
    ortho: str

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

    def parts(self):
        yield from self.morpheme_seq.parts

@final
class MorphemeStressNormalizedKey(NamedTuple):
    name: str
    phono: tuple[Keysymbol, ...]
    max_stress: int
    ortho: str

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

    def __repr__(self):
        return f"Morpheme({self.name} : {self.phono} : {self.ortho})"

@final
@dataclass(frozen=True)
class Formatting:
    parent: "Root | Affix | None"
    name: str
    ortho: str = ""
    @property
    def phono(self):
        return ""

    def parts(self):
        yield from ()


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
    is_morpheme = True

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
        chunks: list[MorphologyChunk] = []

        while self.morphology_index < len(self.morphology):
            if self.morphology_char in "{<>":
                formatting = tuple(self.__check_formatting(None))
                parts.extend(formatting)
                chunks.extend(formatting)

                if self.morphology_char == "{":
                    self.__catch_up_transcription_index("{")
                    root = self.__consume_root()
                    parts.extend(root.morpheme_seq.parts)
                    chunks.append(root)

                elif self.morphology_char == ">":
                    self.__catch_up_transcription_index(">")
                    suffix = self.__consume_suffix()
                    parts.extend(suffix.morpheme_seq.parts)
                    chunks.append(suffix)

                elif self.morphology_char == "<":
                    self.__catch_up_transcription_index("<")
                    prefix = self.__consume_prefix()
                    parts.extend(prefix.morpheme_seq.parts)
                    chunks.append(prefix)

                self.morphology_index_at_last_part = self.morphology_index
                continue
            
            self.morphology_index += 1

        return Morphology(tuple(parts), tuple(chunks))

    
    def __catch_up_transcription_index(self, target_chars: str):
        while self.transcription_char not in target_chars:
            self.transcription_index += 1


    def __check_formatting(self, parent: "Root | Affix | None"):
        if self.morphology_index_at_last_part > self.morphology_index:
            yield Formatting(parent, self.morphology_since_last_part) 


    def __consume_suffix(self):
        self.transcription_index += 1
        self.morphology_index += 1

        suffix = Affix(True)
        self.is_morpheme = True
        while True:
            if self.morphology_char == ">":
                break

            suffix.morpheme_seq.extend(self.__handle_morpheme_boundary(suffix))

        self.__catch_up_transcription_index(">")
        self.transcription_index += 1
        self.morphology_index += 1

        return suffix


    def __consume_prefix(self):
        self.transcription_index += 1
        self.morphology_index += 1

        prefix = Affix(False)
        self.is_morpheme = True
        while True:
            if self.morphology_char == "<":
                break

            prefix.morpheme_seq.extend(self.__handle_morpheme_boundary(prefix))

        self.__catch_up_transcription_index("<")
        self.transcription_index += 1
        self.morphology_index += 1

        return prefix


    def __consume_root(self):
        # {
        self.transcription_index += 1
        self.morphology_index += 1
        
        root = Root()
        self.is_morpheme = True
        while True:
            if self.morphology_char == "}":
                root.morpheme_seq.extend(self.__check_formatting(root))

                self.__catch_up_transcription_index("}")
                self.transcription_index += 1
                self.morphology_index += 1
                break

            root.morpheme_seq.extend(self.__handle_morpheme_boundary(root))


        root.morpheme_seq.extend(self.__check_formatting(root))

        return root


    
    def __handle_morpheme_boundary(self, parent: "Root | Affix") -> "Generator[Formatting | Morpheme, None, None]":
        if self.morphology_char == "=":
            self.is_morpheme = not self.is_morpheme
            if not self.is_morpheme:
                yield from self.__check_formatting(parent)

            self.__catch_up_transcription_index("=")
            self.transcription_index += 1
            self.morphology_index += 1
            self.morphology_index_at_last_part = self.morphology_index
            return

        if self.is_morpheme:
            yield self.__consume_morpheme(parent)
        else:
            self.morphology_index += 1


    def __consume_morpheme(self, parent: "Root | Affix"):
        phono = ""
        while True:
            if self.transcription_char in "=}<>":
                break

            phono += self.transcription_char
            self.transcription_index += 1

        name = ""
        while True:
            if self.morphology_char in "=}<>":
                break

            name += self.morphology_char
            self.morphology_index += 1

        return Morpheme(parent, name, phono.strip())


def split_morphology(transcription: str, morphology: str):
    return _Parser(transcription, morphology).split_morphology()
