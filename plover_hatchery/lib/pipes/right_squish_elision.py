from .banks import BanksPlugin, BanksState


def right_squish_elision():
    def on_complete_vowel(banks_state: BanksState, **_):
        if banks_state.last_right_node is None: return
        banks_state.right_src_nodes += (banks_state.last_right_node,)


    return BanksPlugin(
        on_complete_vowel=on_complete_vowel,
    )