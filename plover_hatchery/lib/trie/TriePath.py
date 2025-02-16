from dataclasses import dataclass
from typing import final
from .Transition import TransitionKey


@final
@dataclass
class TriePath:
    node_id: int
    transitions: tuple[TransitionKey, ...]
    