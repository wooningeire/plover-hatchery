from .banks import banks, BanksState
from .Plugin import define_plugin, GetPluginApi


def left_squish_elision():
    @define_plugin(left_squish_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.on_complete_vowel.listen(left_squish_elision)
        def _(banks_state: BanksState, **_):
            if banks_state.last_left_node is None: return
            banks_state.left_src_nodes += (banks_state.last_left_node,)

        return None

    return plugin

