from plover.steno import Stroke

from ...sophone.Sophone import Sophone, vowel_phonemes
from ...trie import Trie, ReadonlyTrie
from ...theory_defaults.amphitheory import amphitheory

from ..use_manage_state import ManageStateHooks
from ..state import EntryBuilderState, ConsonantVowelGroup, OutlineSounds

from .find_clusters import Cluster, handle_clusters, get_clusters_from_node, check_found_clusters

def use_consonant_clusters(manage_state: ManageStateHooks, clusters: dict[str, str]):
    def build_consonant_clusters_trie() -> ReadonlyTrie[Sophone, Stroke]:
        trie: Trie[Sophone, Stroke] = Trie()
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

        state: EntryBuilderState,
    ):
        current_head = consonant_clusters_trie.ROOT
        current_index = (start_group_index, start_phoneme_index)
        while current_head is not None and current_index is not None:
            current_head = consonant_clusters_trie.get_dst_node(current_head, amphitheory.sound_sophone(sounds.get_consonant(*current_index)))

            if current_head is None: return

            if (result := get_clusters_from_node(current_head, current_index, consonant_clusters_trie, state)) is not None:
                yield result

            current_index = sounds.increment_consonant_index(*current_index)


    upcoming_clusters: dict[tuple[int, int], list[Cluster]]


    @manage_state.begin.listen
    def _():
        nonlocal upcoming_clusters

        upcoming_clusters = {}


    @manage_state.complete_consonant.listen
    def _(state: EntryBuilderState, left_node: "int | None", right_node: "int | None"):
        handle_clusters(upcoming_clusters, state, find_consonant_clusters)

        check_found_clusters(
            upcoming_clusters,
            left_node,
            right_node,
            state,
        )


    @manage_state.complete_nonfinal_group.listen
    def _(state: EntryBuilderState, group: ConsonantVowelGroup, new_stroke_node: int):
        check_found_clusters(
            upcoming_clusters,
            state.left_consonant_src_nodes[0],
            state.right_consonant_src_nodes[0] if len(state.right_consonant_src_nodes) > 0 else None,
            state,
        )
