from plover_hatchery.lib.pipes.Plugin import Plugin


from plover_hatchery.lib.pipes.join import NodeSrc


from .banks import banks, BanksState
from .Plugin import define_plugin, GetPluginApi


def left_squish_elision() -> Plugin[None]:
    @define_plugin(left_squish_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.complete_vowel.listen(left_squish_elision)
        def _(banks_state: BanksState, **_):
            banks_state.left_srcs += tuple(NodeSrc(src.node, 8) for src in banks_state.last_left_nodes)


        return None

    return plugin

