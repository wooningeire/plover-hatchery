from collections.abc import Iterable
from itertools import product
from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from plover.steno import Stroke

from plover_hatchery.lib.pipes.SophoneType import Sophone, SophoneType
from plover_hatchery.lib.pipes.declare_banks import declare_banks

from ..OutlineSounds import OutlineSounds
from ..Plugin import define_plugin, GetPluginApi
from ..banks import banks, BanksState

from ...sopheme import Sound
from ...trie import Trie, ReadonlyTrie

from .find_clusters import Cluster, handle_clusters, get_clusters_from_node, check_found_clusters


@dataclass
class ConsonantClustersState:
    upcoming_clusters: dict[tuple[int, int], list[Cluster]] = field(default_factory=lambda: {})


def consonant_clusters(sophone_type: SophoneType, clusters: dict[str, str], *, base_cost: int) -> Plugin[None]:
    def build_consonant_clusters_trie() -> ReadonlyTrie[Sophone, Stroke]:
        trie: Trie[Sophone, Stroke] = Trie()
        for phonemes, steno in clusters.items():
            current_head = trie.ROOT
            for key in phonemes.split(" "):
                sophone = sophone_type[key]
                current_head = trie.follow(current_head, sophone)

            trie.set_translation(current_head, Stroke.from_steno(steno))
            
        return trie.frozen()
    
    consonant_clusters_trie = build_consonant_clusters_trie()


    @define_plugin(consonant_clusters)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_info = get_plugin_api(declare_banks)
        banks_hooks = get_plugin_api(banks)


        def find_consonant_clusters(
            sounds: OutlineSounds,
            start_group_index: int,
            start_phoneme_index: int,

            state: BanksState,
        ):
            current_heads = (consonant_clusters_trie.ROOT,)
            current_index = (start_group_index, start_phoneme_index)
            while current_index is not None:
                new_current_heads: list[int] = []
                for node, sound in product(current_heads, sophone_type.from_sound(sounds.get_consonant(*current_index))):
                    new_node = consonant_clusters_trie.traverse(node, sound)
                    if new_node is None: continue
                    new_current_heads.append(new_node)
                

                if len(new_current_heads) == 0: return


                current_heads = tuple(new_current_heads)

                for node in current_heads:
                    result = get_clusters_from_node(node, current_index, consonant_clusters_trie, state, banks_info.left)
                    if result is not None:
                        yield result

                current_index = sounds.increment_consonant_index(*current_index)


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
                base_cost,
            )


        @banks_hooks.before_complete_vowel.listen(consonant_clusters)
        def _(state: ConsonantClustersState, banks_state: BanksState, **_):
            check_found_clusters(
                state.upcoming_clusters,
                banks_state.left_srcs[0].node,
                banks_state.right_srcs[0].node if len(banks_state.right_srcs) > 0 else None,
                banks_state,
                base_cost,
            )

        
        return None


    return plugin