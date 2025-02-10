from plover_hatchery.lib.pipes.Plugin import Plugin
from plover_hatchery.lib.pipes.join import NodeSrc
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
            if banks_state.last_right_node is None: return

            new_stroke_node = banks_state.trie.get_first_dst_node_else_create(banks_state.last_right_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, banks_state.entry_id))
            banks_state.left_srcs += (NodeSrc(new_stroke_node, 5),)


        return None

    return plugin
