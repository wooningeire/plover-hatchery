from plover.steno import Stroke

from ..trie import TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY

from .Plugin import GetPluginApi, Plugin, define_plugin
from .banks import banks, BanksState


def linker_chord(chord: str) -> Plugin[None]:
    stroke = Stroke.from_steno(chord)

    @define_plugin(linker_chord)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.before_complete_consonant.listen(linker_chord)
        def _(banks_state: BanksState, left_node: "int | None", right_node: "int | None", **_):
            if left_node is None or right_node is None: return

            sounds = banks_state.sounds
            next_index = sounds.increment_index(banks_state.group_index, banks_state.sound_index)
            if next_index is None: return

            if sounds.is_vowel(*next_index):
                new_stroke_node = banks_state.trie.create_node(right_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, banks_state.translation))
                banks_state.trie.link_chain(new_stroke_node, left_node, stroke.keys(), TransitionCostInfo(0, banks_state.translation))
            else:
                banks_state.trie.link(right_node, left_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, banks_state.translation))


        return None

    return plugin