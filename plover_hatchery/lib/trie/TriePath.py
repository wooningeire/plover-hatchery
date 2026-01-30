from dataclasses import dataclass
from typing import final

from plover_hatchery_lib_rs import TransitionKey


@final
@dataclass
class JoinedTransitionSeq:
    transitions: list[TransitionKey]

@final
@dataclass
class JoinedTriePaths:
    dst_node_id: int | None
    transition_seqs: tuple[JoinedTransitionSeq, ...]