from collections.abc import Callable


class Keysymbol:
    symbol: str
    base_symbol: str
    stress: int = 0
    optional: bool = False

    def __init__(self, symbol: str, stress: int, optional: bool, /) -> None: ...

    @property
    def is_vowel(self) -> bool: ...

    @property
    def is_consonant(self) -> bool: ...


class Sopheme:
    chars: str
    keysymbols: list[Keysymbol]

    def __init__(self, chars: str, keysymbols: list[Keysymbol], /) -> None: ...

    @property
    def can_be_silent(self) -> bool: ...


class Transclusion:
    target_varname: str
    stress: int

    def __init__(self, target_varname: str, stress: int, /) -> None: ...

class Entity:
    @staticmethod
    def sopheme(sopheme: Sopheme, /) -> Entity: ...

    @staticmethod
    def transclusion(transclusion: Transclusion, /) -> Entity: ...

    @property
    def maybe_sopheme(self) -> Sopheme | None: ...

    @property
    def maybe_transclusion(self) -> Transclusion | None: ...


class Definition:
    entities: list[Entity]

    def __init__(self, entities: list[Entity], /) -> None: ...

class DefinitionDictionary:
    def sophemes_in(self, definition: Definition, varname: str, /) -> list[Sopheme]: ...

    def add(self, varname: str, definition: Definition, /) -> None: ...

    def foreach(self, callable: Callable[[str, Definition], None], /) -> None: ...
