from .banks import BanksHooks, BanksState


def left_squish_elision():
    def on_complete_vowel(banks_state: BanksState, **_):
        if banks_state.last_left_node is None: return
        banks_state.left_src_nodes += (banks_state.last_left_node,)


    return BanksHooks(
        on_complete_vowel=on_complete_vowel,
    )