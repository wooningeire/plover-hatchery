from plover.steno import Stroke

from ...sophone.Sophone import Sophone, vowel_phonemes
from ...trie import Trie, ReadonlyTrie, NondeterministicTrie
from ...theory_defaults.amphitheory import amphitheory

from ..state import EntryBuilderState, ConsonantVowelGroup, OutlineSounds

from .find_clusters import Cluster, handle_clusters, get_clusters_from_node, check_found_clusters


def use_vowel_clusters(manage_state: BanksHooks, clusters: dict[str, str]):
    def build_vowel_clusters_trie() -> ReadonlyTrie[Sophone, Stroke]:
        trie: Trie[Sophone, Stroke] = Trie()
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

        state: EntryBuilderState,
    ):
        current_nodes = {vowel_clusters_trie.ROOT}
        current_index = (start_group_index, start_phoneme_index)
        while current_nodes is not None and current_index is not None:
            sound = sounds[current_index]
            current_nodes = {
                node
                for current_node in current_nodes
                for node in (vowel_clusters_trie.get_dst_node(current_node, amphitheory.sound_sophone(sound)),)
                        + ((vowel_clusters_trie.get_dst_node(current_node, Sophone.ANY_VOWEL),) if amphitheory.sound_sophone(sound) in vowel_phonemes else ())
                if node is not None
            }

            if len(current_nodes) == 0: return

            for current_node in current_nodes:
                if (result := get_clusters_from_node(current_node, current_index, vowel_clusters_trie, state)) is None:
                    continue

                yield result

            current_index = sounds.increment_index(*current_index)


    upcoming_clusters: dict[tuple[int, int], list[Cluster]]


    @manage_state.begin.listen
    def _(trie: NondeterministicTrie[str, str]):
        nonlocal upcoming_clusters

        upcoming_clusters = {}


    @manage_state.complete_consonant.listen
    def _(state: EntryBuilderState, left_node: "int | None", right_node: "int | None"):
        check_found_clusters(
            upcoming_clusters,
            left_node,
            right_node,
            state,
        )
    
    
    @manage_state.before_complete_nonfinal_group.listen
    def _(state: EntryBuilderState):
        handle_clusters(upcoming_clusters, state, find_vowel_clusters)

        check_found_clusters(
            upcoming_clusters,
            state.left_consonant_src_nodes[0],
            state.right_consonant_src_nodes[0] if len(state.right_consonant_src_nodes) > 0 else None,
            state,
        )
