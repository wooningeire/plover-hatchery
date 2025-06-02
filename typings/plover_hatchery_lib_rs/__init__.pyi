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

class OverridableEntity:
    ...


class EntitySeq:
    entities: list[Entity]

    def __init__(self, entities: list[Entity], /) -> None: ...

class Def:
    items: list[OverridableEntity]
    varname: str

    def __init__(self, items: list[OverridableEntity], varname: str, /) -> None: ...

class DefDict:
    def add(self, varname: str, definition: EntitySeq, /) -> None: ...
    def get_def(self, varname: str, /) -> Def: ...
    def foreach_key(self, callable: Callable[[str], None], /) -> None: ...


class SophemeSeq:
    sophemes: list[Sopheme]


class DefView:
    defs: DefDict
    base_def: Def

    def __init__(self, defs: DefDict, base_def: Def, /) -> None: ...
    def collect_sophemes(self) -> SophemeSeq: ...
    def translation(self) -> str: ...

# def add_diphthong_transitions(sophemes_by_first_consonant: Callable[[DefCursor], Iterable[Sopheme]]) -> Def: ...