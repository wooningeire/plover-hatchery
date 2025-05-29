from plover_hatchery.lib.sopheme import Sopheme


class Transclusion:
    target_varname: str
    stress: int

    def __init__(self, target_varname: str, stress: int, /) -> None: ...

class Entity:
    @staticmethod
    def sopheme(sopheme: Sopheme) -> Entity: ...

    @staticmethod
    def transclusion(transclusion: Transclusion) -> Entity: ...

    @property
    def maybe_sopheme(self) -> Sopheme | None: ...

    @property
    def maybe_transclusion(self) -> Transclusion | None: ...
