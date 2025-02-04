from .banks import BanksState
from .left_alt_chords import LeftAltChordsPlugin, LeftAltChordsState


def left_alt_squish_elision():
    def on_complete_vowel(left_alt_chords_state: LeftAltChordsState, banks_state: BanksState, **_):
        if left_alt_chords_state.last_left_alt_node is None: return
        banks_state.left_src_nodes += (left_alt_chords_state.last_left_alt_node,)


    return LeftAltChordsPlugin(
        on_complete_vowel=on_complete_vowel,
    )