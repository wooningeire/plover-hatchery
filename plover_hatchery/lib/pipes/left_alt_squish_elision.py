from plover_hatchery.lib.pipes.Plugin import Plugin
from plover_hatchery.lib.pipes.join import NodeSrc

from .banks import BanksState
from .left_alt_chords import left_alt_chords, LeftAltChordsState
from .Plugin import define_plugin, GetPluginApi


def left_alt_squish_elision() -> Plugin[None]:
    @define_plugin(left_alt_squish_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        left_alt_chords_hooks = get_plugin_api(left_alt_chords)

        @left_alt_chords_hooks.complete_vowel.listen(left_alt_squish_elision)
        def _(left_alt_chords_state: LeftAltChordsState, banks_state: BanksState, **_):
            banks_state.left_srcs += tuple(NodeSrc(src.node, 8) for src in left_alt_chords_state.last_left_alt_nodes)


        return None

    return plugin