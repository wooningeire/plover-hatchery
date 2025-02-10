from plover_hatchery.lib.pipes.Plugin import Plugin
from plover_hatchery.lib.pipes.join import NodeSrc, join
from plover_hatchery.lib.trie import TransitionCostInfo

from .banks import banks, BanksState
from .Plugin import define_plugin, GetPluginApi
from ..config import TRIE_STROKE_BOUNDARY_KEY


def boundary_elision() -> Plugin[None]:
    @define_plugin(boundary_elision)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.complete_vowel.listen(boundary_elision)
        def _(banks_state: BanksState, **_):
            new_stroke_node = join(banks_state.trie, banks_state.last_right_nodes, TRIE_STROKE_BOUNDARY_KEY, banks_state.entry_id)

            if new_stroke_node is None: return
            banks_state.left_srcs += (NodeSrc(new_stroke_node, 5),)


        return None

    return plugin
