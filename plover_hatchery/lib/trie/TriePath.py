from dataclasses import dataclass
from typing import final

from .Transition import TransitionKey


@final
@dataclass
class TriePath:
    dst_node_id: int = 0
    transitions: tuple[TransitionKey, ...] = ()


@final
@dataclass
class JoinedTransitionSeq:
    transitions: tuple[TransitionKey, ...]

@final
@dataclass
class JoinedTriePaths:
    dst_node_id: int | None
    transition_seqs: tuple[JoinedTransitionSeq, ...]