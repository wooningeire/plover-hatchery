from plover.steno import Stroke

from ..trie import TransitionCostInfo
from .state import EntryBuilderState, ConsonantVowelGroup
from .use_manage_state import ManageStateHooks


def use_initial_vowel_chord(manage_state: ManageStateHooks, initial_vowel_chord: str):
    stroke = Stroke.from_steno(initial_vowel_chord)

    @manage_state.complete_nonfinal_group.listen
    def _(state: EntryBuilderState, group: ConsonantVowelGroup, new_stroke_node: int):
        if not state.is_first_consonant_set or len(group.consonants) > 0: return

        state.trie.link_chain(
            state.trie.ROOT,
            new_stroke_node,
            stroke.keys(),
            TransitionCostInfo(0, state.translation)
        )
