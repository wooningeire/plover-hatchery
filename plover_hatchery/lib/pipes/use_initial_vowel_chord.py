from plover.steno import Stroke

from ..trie import TransitionCostInfo
from .state import EntryBuilderState, ConsonantVowelGroup
from .banks import BanksPlugin

def use_initial_vowel_chord(initial_vowel_chord: str):
    stroke = Stroke.from_steno(initial_vowel_chord)

    def on_vowel_complete(group: ConsonantVowelGroup, new_stroke_node: int | None):
        if not state.is_first_consonant_set or len(group.consonants) > 0 or new_stroke_node is None: return

        state.trie.link_chain(
            state.trie.ROOT,
            new_stroke_node,
            stroke.keys(),
            TransitionCostInfo(0, state.translation)
        )

    return BanksPlugin(
        on_vowel_complete=on_vowel_complete,
    )
