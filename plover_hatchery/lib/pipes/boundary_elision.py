from .banks import banks, BanksState
from .Plugin import define_plugin, GetPluginApi


def boundary_elision():
    @define_plugin(boundary_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.on_complete_vowel.listen(boundary_elision)
        def _(banks_state: BanksState, **_):
            banks_state.left_src_nodes += banks_state.mid_src_nodes

        return None

    return plugin
