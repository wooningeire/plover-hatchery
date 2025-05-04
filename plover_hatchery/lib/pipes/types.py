
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

    def __repr__(self):
        return f"Soph({self.value})"

    @staticmethod
    def parse_seq(soph_values: str):
        return tuple(Soph(value) for value in soph_values.split())