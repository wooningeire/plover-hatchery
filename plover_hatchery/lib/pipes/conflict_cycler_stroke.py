from typing import Any


from dataclasses import dataclass
from plover.steno import Stroke

from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.soph_trie import LookupResultWithAssociations, soph_trie
from plover_hatchery.lib.pipes.types import EntryIndex
from plover_hatchery.lib.trie import LookupResult


def conflict_cycler_stroke(steno: str) -> Plugin[None]:
    cycler_stroke = Stroke.from_steno(steno)

    @define_plugin(conflict_cycler_stroke)
    def plugin(get_plugin_api: GetPluginApi, **_):
        soph_trie_api = get_plugin_api(soph_trie)


        @dataclass
        class ConflictCyclerStrokeState:
            conflict_index: int = -1


        @soph_trie_api.begin_lookup.listen(conflict_cycler_stroke)
        def _(**_):
            return ConflictCyclerStrokeState()


        @soph_trie_api.process_outline.listen(conflict_cycler_stroke)
        def _(state: ConflictCyclerStrokeState, outline: tuple[Stroke, ...], **_):
            index_of_first_cycler_stroke = 0

            for i in range(len(outline) - 1, -1, -1):
                if outline[i] == cycler_stroke:
                    continue

                index_of_first_cycler_stroke = i + 1
                break


            state.conflict_index = len(outline) - index_of_first_cycler_stroke

            return outline[:index_of_first_cycler_stroke]

        
        @soph_trie_api.select_translation.listen(conflict_cycler_stroke)
        def _(
            state: ConflictCyclerStrokeState,
            choices: list[LookupResultWithAssociations],
            translations: list[str],
            **_,
        ):
            return translations[choices[state.conflict_index % len(choices)].lookup_result.translation.value]

            # if len(positionless) == 0:
            #     return nth_variation(translation_choices, n_variation, translations)
            # else:
            #     for transition in reversed(first_choice.transitions):
            #         if trie.transition_has_key(transition, TRIE_STROKE_BOUNDARY_KEY): break
            #         if not trie.transition_has_key(transition, banks_info.positionless.rtfcre): continue

            #         return nth_variation(translation_choices, n_variation, translations)

            # return nth_variation(translation_choices, n_variation + 1, translations) if len(translation_choices) > 1 else None

        
        return None


    return plugin