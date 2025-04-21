from plover_hatchery.lib.pipes.Plugin import Plugin


from dataclasses import dataclass, field

from plover.steno import Stroke

from plover_hatchery.lib.pipes.SophoneType import Sophone, SophoneType
from plover_hatchery.lib.pipes.declare_banks import declare_banks

from ...trie import Trie, ReadonlyTrie

from ..Plugin import define_plugin, GetPluginApi
from ..banks import banks, BanksState

from .find_clusters import Cluster, handle_clusters, get_clusters_from_clusters_trie_node, check_found_clusters


@dataclass
class VowelClustersState:
    upcoming_clusters: dict[tuple[int, int], list[Cluster]] = field(default_factory=lambda: {})


def vowel_clusters(sophone_type: SophoneType, vowel_sophones: set[Sophone], clusters: dict[str, str], base_cost: int) -> Plugin[None]:
    def build_vowel_clusters_trie() -> "ReadonlyTrie[Sophone | None, Stroke]":
        trie: "Trie[Sophone | None, Stroke]" = Trie()
        for phonemes, steno in clusters.items():
            current_head = trie.ROOT
            for key in phonemes.split(" "):
                if key == ".":
                    sophone = None
                else:
                    sophone = sophone_type[key]
                current_head = trie.follow(current_head, sophone)

            trie.set_translation(current_head, Stroke.from_steno(steno))
            
        return trie.frozen()
    
    vowel_clusters_trie = build_vowel_clusters_trie()



    @define_plugin(vowel_clusters)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_info = get_plugin_api(declare_banks)
        banks_hooks = get_plugin_api(banks)


        def find_vowel_clusters_ending_at(state: BanksState):
            current_nodes = {vowel_clusters_trie.ROOT}
            current_phoneme = state.current_phoneme
            while current_phoneme is not None:
                current_nodes = {
                    node
                    for current_node in current_nodes
                    for node in tuple(vowel_clusters_trie.traverse(current_node, sophone) for sophone in sophone_type.from_phoneme(current_phoneme))
                        + ((vowel_clusters_trie.traverse(current_node, None),) if any(sophone in vowel_sophones for sophone in sophone_type.from_phoneme(current_phoneme)) else ())
                    if node is not None
                }

                if len(current_nodes) == 0: return

                for current_node in current_nodes:
                    result = get_clusters_from_clusters_trie_node(
                        current_node,
                        current_phoneme,
                        vowel_clusters_trie,
                        state,
                        banks_info
                    )
                    if result is None:
                        continue

                    yield result

                current_phoneme = current_phoneme.next()


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
                base_cost,
            )
        
        
        @banks_hooks.before_complete_vowel.listen(vowel_clusters)
        def _(state: VowelClustersState, banks_state: BanksState, **_):
            handle_clusters(state.upcoming_clusters, banks_state, find_vowel_clusters_ending_at)

            check_found_clusters(
                state.upcoming_clusters,
                banks_state.left_srcs[0].node,
                banks_state.right_srcs[0].node if len(banks_state.right_srcs) > 0 else None,
                banks_state,
                base_cost,
            )


        return None
    
    return plugin
