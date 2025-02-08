from plover.steno import Stroke

from ..trie import TransitionCostInfo
from .banks import BanksHooks, BanksState

def initial_vowel_chord(initial_vowel_chord: str):
    stroke = Stroke.from_steno(initial_vowel_chord)

    def on_complete_vowel(banks_state: BanksState, group_index: int, sound_index: int, new_stroke_node: int, **_):
        if group_index > 0 or sound_index > 0: return

        banks_state.trie.link_chain(
            banks_state.trie.ROOT,
            new_stroke_node,
            stroke.keys(),
            TransitionCostInfo(0, banks_state.translation)
        )

    return BanksHooks(
        on_complete_vowel=on_complete_vowel,
    )
