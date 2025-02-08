from plover.steno import Stroke

from ..trie import TransitionCostInfo
from .banks import BanksState, banks
from .Plugin import define_plugin, GetPluginApi

def initial_vowel_chord(chord: str):
    stroke = Stroke.from_steno(chord)


    this_id = id(initial_vowel_chord)
    
    @define_plugin(this_id)
    def initialize(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.on_complete_vowel.listen(this_id)
        def _(banks_state: BanksState, group_index: int, sound_index: int, new_stroke_node: int, **_):
            if group_index > 0 or sound_index > 0: return

            banks_state.trie.link_chain(
                banks_state.trie.ROOT,
                new_stroke_node,
                stroke.keys(),
                TransitionCostInfo(0, banks_state.translation)
            )

        return None
    
    return initialize
