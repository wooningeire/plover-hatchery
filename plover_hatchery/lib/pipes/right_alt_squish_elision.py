from plover_hatchery.lib.pipes.Plugin import Plugin

from .banks import BanksState
from .right_alt_chords import right_alt_chords, RightAltChordsState
from .Plugin import define_plugin, GetPluginApi


def right_alt_squish_elision() -> Plugin[None]:
    @define_plugin(right_alt_squish_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        right_alt_chords_hooks = get_plugin_api(right_alt_chords)

        @right_alt_chords_hooks.complete_vowel.listen(right_alt_squish_elision)
        def _(right_alt_chords_state: RightAltChordsState, banks_state: BanksState, **_):
            if right_alt_chords_state.last_right_alt_node is None: return
            banks_state.right_src_nodes += (right_alt_chords_state.last_right_alt_node,)


        return None

    return plugin