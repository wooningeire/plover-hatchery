from dataclasses import dataclass
from typing import final
from plover.steno import Stroke

from plover_hatchery.lib.pipes.join import tuplify

from ..trie import TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY

from .Plugin import GetPluginApi, Plugin, define_plugin
from .banks import banks, BanksState


@final
@dataclass
class LinkerChordState:
    newest_new_stroke_node: "int | None" = None
    newest_post_linker_node: "int | None" = None


def linker_chord(chord: str) -> Plugin[None]:
    stroke = Stroke.from_steno(chord)

    @define_plugin(linker_chord)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.begin.listen(linker_chord)
        def _():
            return LinkerChordState()


        @banks_hooks.before_complete_consonant.listen(linker_chord)
        def _(state: LinkerChordState, banks_state: BanksState, left_node: "int | None", right_node: "int | None", **_):
            if left_node is None or right_node is None: return


            current_phoneme = banks_state.current_phoneme
            if current_phoneme is None: return

            current_phoneme = current_phoneme.next()


            new_stroke_node = banks_state.trie.follow(right_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, banks_state.entry_id)).dst_node_id


            while current_phoneme is not None:
                if current_phoneme.keysymbol.is_vowel:
                    post_linker_node = banks_state.trie.follow_chain(new_stroke_node, stroke.keys(), TransitionCostInfo(0, banks_state.entry_id)).dst_node_id

                    state.newest_post_linker_node = post_linker_node

                    break

                if not current_phoneme.keysymbol.optional:
                    break

                current_phoneme = current_phoneme.next()

            state.newest_new_stroke_node = new_stroke_node

        @banks_hooks.complete_consonant.listen(linker_chord)
        def _(state: LinkerChordState, banks_state: BanksState, **_):
            banks_state.left_srcs += tuplify(state.newest_new_stroke_node)
            banks_state.mid_srcs += tuplify(state.newest_post_linker_node)


            state.newest_new_stroke_node = None
            state.newest_post_linker_node = None


        return None

    return plugin