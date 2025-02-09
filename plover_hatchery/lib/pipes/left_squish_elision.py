from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Any

from plover_hatchery.lib.pipes.join import NodeSrc


from .banks import banks, BanksState
from .Plugin import define_plugin, GetPluginApi


def left_squish_elision() -> Plugin[None]:
    @define_plugin(left_squish_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.complete_vowel.listen(left_squish_elision)
        def _(banks_state: BanksState, **_):
            if banks_state.last_left_node is None: return
            banks_state.left_srcs += (NodeSrc(banks_state.last_left_node, 8),)


        return None

    return plugin

