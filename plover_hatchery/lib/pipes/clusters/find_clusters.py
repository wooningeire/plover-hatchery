import dataclasses
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable

from plover.steno import Stroke

from ..state import OutlineSounds
from ..banks import BanksState

from ...trie import NondeterministicTrie, TransitionCostInfo, ReadonlyTrie
from ...theory_defaults.amphitheory import amphitheory




@dataclass(frozen=True)
class Cluster(ABC):
    stroke: Stroke
    initial_state: BanksState

    @abstractmethod
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: "int | None", current_right: "int | None"):
        ...

@dataclass(frozen=True)
class _ClusterLeft(Cluster):
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: "int | None", current_right: "int | None"):
        if current_left is None: return

        state = self.initial_state

        if len(state.left_src_nodes) > 0:
            trie.link_chain(state.left_src_nodes[0], current_left, self.stroke.keys(), TransitionCostInfo(amphitheory.spec.TransitionCosts.CLUSTER, translation))

        # if state.can_elide_prev_vowel_left:
        #     state.left_squish_elision.execute(state.trie, state.translation, current_left, self.stroke, amphitheory.spec.TransitionCosts.CLUSTER)
        #     state.boundary_elision.execute(state.trie, state.translation, current_left, self.stroke, amphitheory.spec.TransitionCosts.CLUSTER)

@dataclass(frozen=True)
class _ClusterRight(Cluster):
    def apply(self, trie: NondeterministicTrie[str, str], translation: str, current_left: "int | None", current_right: "int | None"):
        if current_right is None: return

        state = self.initial_state

        if len(self.initial_state.right_src_nodes) > 0:
            trie.link_chain(self.initial_state.right_src_nodes[0], current_right, self.stroke.keys(), TransitionCostInfo(amphitheory.spec.TransitionCosts.CLUSTER, translation))

        # if self.initial_state.is_first_consonant:
        #     state.left_squish_elision.execute(state.trie, state.translation, current_right, self.stroke, amphitheory.spec.TransitionCosts.CLUSTER)


        # if origin.right_f is not None and right_consonant_f_node is not None:
        #     trie.link_chain(origin.right_f, right_consonant_f_node, cluster_stroke.keys(), TransitionCosts.CLUSTER, translation)

        # if is_first_consonant:
        #     _allow_elide_previous_vowel_using_first_right_consonant(
        #         trie, cluster_stroke, right_consonant_f_node, origin.pre_rtl_stroke_boundary, translation, TransitionCosts.CLUSTER + TransitionCosts.F_CONSONANT,
        #     )

def get_clusters_from_node(
    node: int,
    current_index: tuple[int, int],
    clusters_trie: ReadonlyTrie[Any, Stroke],

    state: BanksState,
):
    stroke = clusters_trie.get_translation(node)
    if stroke is None: return None

    if len(stroke & amphitheory.spec.LEFT_BANK_CONSONANTS_SUBSTROKE) > 0:
        return current_index, _ClusterLeft(stroke, state.clone())
    else:
        return current_index, _ClusterRight(stroke, state.clone())
    

def handle_clusters(
    upcoming_clusters: dict[tuple[int, int], list[Cluster]],
    
    state: BanksState,

    find_clusters: "Callable[[OutlineSounds, int, int, BanksState], Iterable[tuple[tuple[int, int], Cluster]]]",
):
    for index, cluster in find_clusters(state.sounds, state.group_index, state.sound_index, state):
        if index not in upcoming_clusters:
            upcoming_clusters[index] = [cluster]
        else:
            upcoming_clusters[index].append(cluster)


def check_found_clusters(
    upcoming_clusters: dict[tuple[int, int], list[Cluster]],
    left_consonant_node: "int | None",
    right_consonant_node: "int | None",
    
    state: BanksState,
):
    if (state.group_index, state.sound_index) not in upcoming_clusters: return
    
    for cluster in upcoming_clusters[state.group_index, state.sound_index]:
        cluster.apply(state.trie, state.translation, left_consonant_node, right_consonant_node)