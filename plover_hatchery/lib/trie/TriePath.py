from dataclasses import dataclass
from typing import final
from .Transition import Transition


@final
@dataclass
class TriePath:
    node_id: int
    transitions: tuple[Transition, ...]
    