from .banks import BanksHooks, BanksState


def boundary_elision():
    def on_complete_vowel(banks_state: BanksState, **_):
        banks_state.left_src_nodes += banks_state.mid_src_nodes


    return BanksHooks(
        on_complete_vowel=on_complete_vowel,
    )