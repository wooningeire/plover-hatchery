from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable

from plover.steno import Stroke

from plover_hatchery.lib.pipes.declare_banks import BankStrokes
from plover_hatchery.lib.sopheme.SophemeSeq import SophemeSeqPhoneme

from ..banks import BanksApi, BanksState

from ...trie import NondeterministicTrie, TransitionCostInfo, ReadonlyTrie




@dataclass(frozen=True)
class Cluster:
    stroke: Stroke
    initial_state: BanksState
    banks_info: BankStrokes

    @abstractmethod
    def apply(self, trie: NondeterministicTrie[str, int], entry_id: int, current_left: "int | None", current_right: "int | None", cost: int):
        if len(self.stroke & (self.banks_info.mid | self.banks_info.right)) > 0: # TODO verify this
            dst_node = current_right
        else:
            dst_node = current_left

        if dst_node is None: return


        if len(self.stroke & self.banks_info.left) > 0:
            node_srcs = self.initial_state.left_srcs
        elif len(self.stroke & self.banks_info.mid) > 0:
            node_srcs = self.initial_state.mid_srcs
        else:
            node_srcs = self.initial_state.right_srcs


        for src in node_srcs:
            _ = trie.link_chain(src.node, dst_node, self.stroke.keys(), TransitionCostInfo(cost, entry_id))



def get_clusters_from_clusters_trie_node(
    node: int,
    current_phoneme: SophemeSeqPhoneme,
    clusters_trie: ReadonlyTrie[Any, Stroke],

    state: BanksState,

    banks_info: BankStrokes,
):
    stroke = clusters_trie.get_translation(node)
    if stroke is None: return None

    return current_phoneme.indices, Cluster(stroke, state.clone(), banks_info)
    

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