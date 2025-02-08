from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from plover.steno import Stroke

from ...trie import Trie, ReadonlyTrie
from ...sopheme import Sound

from ..Plugin import define_plugin, GetPluginApi
from ..state import OutlineSounds
from ..banks import banks, BanksState

from .find_clusters import Cluster, handle_clusters, get_clusters_from_node, check_found_clusters


@dataclass
class VowelClustersState:
    upcoming_clusters: dict[tuple[int, int], list[Cluster]] = field(default_factory=lambda: {})


def vowel_clusters(Sophone: Enum, map_sophones: Callable[[Sound], Any], vowel_sophones: set[Any], clusters: dict[str, str]) -> Plugin[None]:
    def build_vowel_clusters_trie() -> ReadonlyTrie[Any, Stroke]:
        trie: Trie[Any, Stroke] = Trie()
        for phonemes, steno in clusters.items():
            current_head = trie.ROOT
            for key in phonemes.split(" "):
                if key == ".":
                    sophone = Sophone.ANY_VOWEL
                else:
                    sophone = Sophone.__dict__[key]
                current_head = trie.get_dst_node_else_create(current_head, sophone)

            trie.set_translation(current_head, Stroke.from_steno(steno))
            
        return trie.frozen()
    
    vowel_clusters_trie = build_vowel_clusters_trie()


    def find_vowel_clusters(
        sounds: OutlineSounds,
        start_group_index: int,
        start_phoneme_index: int,

        state: BanksState,
    ):
        current_nodes = {vowel_clusters_trie.ROOT}
        current_index = (start_group_index, start_phoneme_index)
        while current_nodes is not None and current_index is not None:
            sound = sounds[current_index]
            current_nodes = {
                node
                for current_node in current_nodes
                for node in (vowel_clusters_trie.get_dst_node(current_node, map_sophones(sound)),)
                        + ((vowel_clusters_trie.get_dst_node(current_node, Sophone.ANY_VOWEL),) if map_sophones(sound) in vowel_sophones else ())
                if node is not None
            }

            if len(current_nodes) == 0: return

            for current_node in current_nodes:
                if (result := get_clusters_from_node(current_node, current_index, vowel_clusters_trie, state)) is None:
                    continue

                yield result

            current_index = sounds.increment_index(*current_index)



    @define_plugin(vowel_clusters)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.begin.listen(vowel_clusters)
        def _():
            return VowelClustersState()


        @banks_hooks.before_complete_consonant.listen(vowel_clusters)
        def _(state: VowelClustersState, banks_state: BanksState, left_node: "int | None", right_node: "int | None", **_):
            check_found_clusters(
                state.upcoming_clusters,
                left_node,
                right_node,
                banks_state,
            )
        
        
        @banks_hooks.before_complete_vowel.listen(vowel_clusters)
        def _(state: VowelClustersState, banks_state: BanksState, **_):
            handle_clusters(state.upcoming_clusters, banks_state, find_vowel_clusters)

            check_found_clusters(
                state.upcoming_clusters,
                banks_state.left_src_nodes[0],
                banks_state.right_src_nodes[0] if len(banks_state.right_src_nodes) > 0 else None,
                banks_state,
            )


        return None
    
    return plugin
