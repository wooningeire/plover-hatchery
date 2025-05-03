
from dataclasses import dataclass
from typing import final


@final
@dataclass(frozen=True)
class EntryIndex:
    value: int

@final
@dataclass(frozen=True)
class Soph:
    value: str