from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Any


from .banks import banks, BanksState
from .Plugin import define_plugin, GetPluginApi


def boundary_elision() -> Plugin[None]:
    @define_plugin(boundary_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.complete_vowel.listen(boundary_elision)
        def _(banks_state: BanksState, **_):
            banks_state.left_src_nodes += banks_state.mid_src_nodes


        return None

    return plugin
