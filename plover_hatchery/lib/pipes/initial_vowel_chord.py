from plover_hatchery.lib.pipes.Plugin import Plugin


from plover.steno import Stroke

from plover_hatchery.lib.sopheme import SophemeSeqPhoneme

from ..trie import TransitionCostInfo
from .banks import BanksState, banks
from .Plugin import define_plugin, GetPluginApi

def initial_vowel_chord(chord: str) -> Plugin[None]:
    stroke = Stroke.from_steno(chord)

    @define_plugin(initial_vowel_chord)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.complete_vowel.listen(initial_vowel_chord)
        def _(banks_state: BanksState, phoneme: SophemeSeqPhoneme, new_stroke_node: "int | None", **_):
            if phoneme.sopheme_index > 0 or phoneme.keysymbol_index > 0 or new_stroke_node is None: return

            _ = banks_state.trie.link_chain(
                banks_state.trie.ROOT,
                new_stroke_node,
                stroke.keys(),
                TransitionCostInfo(0, banks_state.entry_id)
            )

        return None
    
    return plugin
