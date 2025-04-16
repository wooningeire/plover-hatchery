from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable

from plover.steno import Stroke

from plover_hatchery.lib.sopheme.SophemeSeq import SophemeSeqPhoneme

from ..banks import BanksState

from ...trie import NondeterministicTrie, TransitionCostInfo, ReadonlyTrie




@dataclass(frozen=True)
class Cluster(ABC):
    stroke: Stroke
    initial_state: BanksState

    @abstractmethod
    def apply(self, trie: NondeterministicTrie[str, int], entry_id: int, current_left: "int | None", current_right: "int | None", cost: int):
        ...

@dataclass(frozen=True)
class _ClusterLeft(Cluster):
    def apply(self, trie: NondeterministicTrie[str, int], entry_id: int, current_left: "int | None", current_right: "int | None", cost: int):
        if current_left is None: return

        state = self.initial_state

        for left_src in state.left_srcs:
            trie.link_chain(left_src.node, current_left, self.stroke.keys(), TransitionCostInfo(cost, entry_id))

        # if state.can_elide_prev_vowel_left:
        #     state.left_squish_elision.execute(state.trie, state.translation, current_left, self.stroke, amphitheory.spec.TransitionCosts.CLUSTER)
        #     state.boundary_elision.execute(state.trie, state.translation, current_left, self.stroke, amphitheory.spec.TransitionCosts.CLUSTER)

@dataclass(frozen=True)
class _ClusterRight(Cluster):
    def apply(self, trie: NondeterministicTrie[str, int], entry_id: int, current_left: "int | None", current_right: "int | None", cost: int):
        if current_right is None: return

        state = self.initial_state

        for right_src in state.right_srcs:
            trie.link_chain(right_src.node, current_right, self.stroke.keys(), TransitionCostInfo(cost, entry_id))

        # if self.initial_state.is_first_consonant:
        #     state.left_squish_elision.execute(state.trie, state.translation, current_right, self.stroke, amphitheory.spec.TransitionCosts.CLUSTER)


        # if origin.right_f is not None and right_consonant_f_node is not None:
        #     trie.link_chain(origin.right_f, right_consonant_f_node, cluster_stroke.keys(), TransitionCosts.CLUSTER, translation)

        # if is_first_consonant:
        #     _allow_elide_previous_vowel_using_first_right_consonant(
        #         trie, cluster_stroke, right_consonant_f_node, origin.pre_rtl_stroke_boundary, translation, TransitionCosts.CLUSTER + TransitionCosts.F_CONSONANT,
        #     )

def get_clusters_from_clusters_trie_node(
    node: int,
    current_phoneme: SophemeSeqPhoneme,
    clusters_trie: ReadonlyTrie[Any, Stroke],

    state: BanksState,

    left_bank: Stroke,
):
    stroke = clusters_trie.get_translation(node)
    if stroke is None: return None

    if len(stroke & left_bank) > 0:
        return current_phoneme.indices, _ClusterLeft(stroke, state.clone())
    else:
        return current_phoneme.indices, _ClusterRight(stroke, state.clone())
    

def handle_clusters(
    upcoming_clusters: dict[tuple[int, int], list[Cluster]],
    
    state: BanksState,

    find_clusters_ending_at: "Callable[[BanksState], Iterable[tuple[tuple[int, int], Cluster]]]",
):
    for index, cluster in find_clusters_ending_at(state):
        if index not in upcoming_clusters:
            upcoming_clusters[index] = [cluster]
        else:
            upcoming_clusters[index].append(cluster)


def check_found_clusters(
    upcoming_clusters: dict[tuple[int, int], list[Cluster]],
    left_consonant_node: "int | None",
    right_consonant_node: "int | None",
    
    state: BanksState,
    cost: int,
):
    current_phoneme = state.current_phoneme
    if current_phoneme is None: return

    if current_phoneme.indices not in upcoming_clusters: return
    
    for cluster in upcoming_clusters[current_phoneme.indices]:
        cluster.apply(state.trie, state.entry_id, left_consonant_node, right_consonant_node, cost)