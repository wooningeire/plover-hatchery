from plover.steno import Stroke

from ..trie import TransitionCostInfo
from .state import EntryBuilderState, ConsonantVowelGroup


def use_initial_vowel_chord(manage_state: BanksHooks, initial_vowel_chord: str):
    stroke = Stroke.from_steno(initial_vowel_chord)

    @manage_state.complete_nonfinal_group.listen
    def _(state: EntryBuilderState, group: ConsonantVowelGroup, new_stroke_node: int | None):
        if not state.is_first_consonant_set or len(group.consonants) > 0 or new_stroke_node is None: return

        state.trie.link_chain(
            state.trie.ROOT,
            new_stroke_node,
            stroke.keys(),
            TransitionCostInfo(0, state.translation)
        )
