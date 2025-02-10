from plover_hatchery.lib.pipes.Plugin import Plugin
from plover_hatchery.lib.pipes.join import NodeSrc

from .banks import BanksState
from .right_alt_chords import right_alt_chords, RightAltChordsState
from .Plugin import define_plugin, GetPluginApi


def right_alt_squish_elision() -> Plugin[None]:
    @define_plugin(right_alt_squish_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        right_alt_chords_hooks = get_plugin_api(right_alt_chords)

        @right_alt_chords_hooks.complete_vowel.listen(right_alt_squish_elision)
        def _(right_alt_chords_state: RightAltChordsState, banks_state: BanksState, **_):
            banks_state.right_srcs += tuple(NodeSrc(src.node, 8) for src in right_alt_chords_state.last_right_alt_nodes)


        return None

    return plugin