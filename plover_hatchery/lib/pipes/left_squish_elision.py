from .banks import BanksPlugin, BanksState


def left_squish_elision():
    def on_complete_vowel(banks_state: BanksState, **_):
        banks_state.left_src_nodes += banks_state.mid_src_nodes


    return BanksPlugin(
        on_complete_vowel=on_complete_vowel,
    )