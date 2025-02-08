from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from plover.steno import Stroke

from ..state import OutlineSounds
from ..Plugin import define_plugin, GetPluginApi
from ..banks import banks, BanksState

from ...sopheme import Sound
from ...trie import Trie, ReadonlyTrie

from .find_clusters import Cluster, handle_clusters, get_clusters_from_node, check_found_clusters


@dataclass
class ConsonantClustersState:
    upcoming_clusters: dict[tuple[int, int], list[Cluster]] = field(default_factory=lambda: {})


def consonant_clusters(Sophone: Enum, map_sophones: Callable[[Sound], Any], clusters: dict[str, str]) -> Plugin[None]:
    def build_consonant_clusters_trie() -> ReadonlyTrie[Any, Stroke]:
        trie: Trie[Any, Stroke] = Trie()
        for phonemes, steno in clusters.items():
            current_head = trie.ROOT
            for key in phonemes.split(" "):
                sophone = Sophone.__dict__[key]
                current_head = trie.get_dst_node_else_create(current_head, sophone)

            trie.set_translation(current_head, Stroke.from_steno(steno))
            
        return trie.frozen()
    
    consonant_clusters_trie = build_consonant_clusters_trie()


    def find_consonant_clusters(
        sounds: OutlineSounds,
        start_group_index: int,
        start_phoneme_index: int,

        state: BanksState,
    ):
        current_head = consonant_clusters_trie.ROOT
        current_index = (start_group_index, start_phoneme_index)
        while current_head is not None and current_index is not None:
            current_head = consonant_clusters_trie.get_dst_node(current_head, map_sophones(sounds.get_consonant(*current_index)))

            if current_head is None: return

            if (result := get_clusters_from_node(current_head, current_index, consonant_clusters_trie, state)) is not None:
                yield result

            current_index = sounds.increment_consonant_index(*current_index)


    @define_plugin(consonant_clusters)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.begin.listen(consonant_clusters)
        def _():
            return ConsonantClustersState()


        @banks_hooks.before_complete_consonant.listen(consonant_clusters)
        def _(state: ConsonantClustersState, banks_state: BanksState, left_node: "int | None", right_node: "int | None", **_):
            handle_clusters(state.upcoming_clusters, banks_state, find_consonant_clusters)

            check_found_clusters(
                state.upcoming_clusters,
                left_node,
                right_node,
                banks_state,
            )


        @banks_hooks.before_complete_vowel.listen(consonant_clusters)
        def _(state: ConsonantClustersState, banks_state: BanksState, **_):
            check_found_clusters(
                state.upcoming_clusters,
                banks_state.left_src_nodes[0],
                banks_state.right_src_nodes[0] if len(banks_state.right_src_nodes) > 0 else None,
                banks_state,
            )

        
        return None


    return plugin