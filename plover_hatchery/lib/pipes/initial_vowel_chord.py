from plover.steno import Stroke

from ..trie import TransitionCostInfo, NondeterministicTrie
from .state import EntryBuilderState, ConsonantVowelGroup
from .banks import BanksPlugin

def initial_vowel_chord(initial_vowel_chord: str):
    stroke = Stroke.from_steno(initial_vowel_chord)

    def on_vowel_complete(trie: NondeterministicTrie[str, str], translation: str, group_index: int, sound_index: int, new_stroke_node: int):
        if group_index > 0 or sound_index > 0: return

        trie.link_chain(
            trie.ROOT,
            new_stroke_node,
            stroke.keys(),
            TransitionCostInfo(0, translation)
        )

    return BanksPlugin(
        on_vowel_complete=on_vowel_complete,
    )
