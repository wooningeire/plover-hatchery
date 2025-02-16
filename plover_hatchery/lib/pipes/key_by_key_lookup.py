
from collections.abc import Iterable
from typing import final
from plover.steno import Stroke

from plover_hatchery.lib.config import TRIE_STROKE_BOUNDARY_KEY
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.declare_banks import declare_banks
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, TransitionKey, TriePath


# @final
# class KeyByKeyLookupApi:




def key_by_key_lookup(
    *,
    cycle_on: "str | None"=None,
    debug_on: "str | None"="",
    prohibit_strokes: Iterable[str]=(),
) -> Plugin[None]:
    cycler_stroke = Stroke.from_steno(cycle_on) if cycle_on is not None else None
    debug_stroke = Stroke.from_steno(debug_on) if debug_on is not None else None

    prohibited_strokes = tuple(Stroke.from_steno(steno) for steno in prohibit_strokes)


    @define_plugin(key_by_key_lookup)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_) -> None:
        banks_info = get_plugin_api(declare_banks)


        @base_hooks.lookup.listen(key_by_key_lookup)
        def _(trie: NondeterministicTrie[str, int], stroke_stenos: tuple[str, ...], translations: list[str], **_) -> "str | None":
            # plover.log.debug("")
            # plover.log.debug("new lookup")

            current_nodes = [TriePath(trie.ROOT, ())]
            n_variation = 0
            debug = False

            positionless = Stroke.from_integer(0)

            for i, stroke_steno in enumerate(stroke_stenos):
                stroke = Stroke.from_steno(stroke_steno)
                if len(stroke) == 0:
                    return None

                # The debug stroke must be the last stroke of the outline if present
                if debug_stroke is not None and i == len(stroke_stenos) - 1 and stroke == debug_stroke:
                    debug = True
                    break
                
                # Increase the variation number for each cycler stroke
                if cycler_stroke is not None and stroke == cycler_stroke:
                    n_variation += 1
                    continue
                # if stroke == CYCLER_STROKE_BACKWARD:
                #     n_variation -= 1
                #     continue
                
                if stroke not in banks_info.all:
                    return None
                
                if stroke in prohibited_strokes:
                    return None

                # A series of cycler strokes should follow any strokes that comprise the word if present
                if n_variation > 0:
                    return None
                

                # Traverse stroke boundaries
                if i > 0:
                    # plover.log.debug(current_nodes)
                    # plover.log.debug(TRIE_STROKE_BOUNDARY_KEY)
                    current_nodes = list(trie.traverse(current_nodes, TRIE_STROKE_BOUNDARY_KEY))
                    if len(current_nodes) == 0:
                        return None

                left_bank_consonants, vowels, right_bank_consonants, positionless = banks_info.split_stroke_parts(stroke)


                for positionless_key in positionless.keys():
                    current_nodes.extend(trie.traverse_chain(current_nodes, positionless_key))


                for key in (left_bank_consonants + vowels + right_bank_consonants).keys():
                    current_nodes = list(trie.traverse(current_nodes, key))
                    for positionless_key in positionless.keys():
                        current_nodes.extend(trie.traverse_chain(current_nodes, positionless_key))

                    if len(current_nodes) == 0:
                        return None

                    
            translation_choices = sorted(trie.get_translations_and_costs(current_nodes), key=lambda result: result.cost)
            if len(translation_choices) == 0: return None

            
            if debug:
                return _join_all_translations(trie, translation_choices, translations)


            first_choice = translation_choices[0]
            if len(positionless) == 0:
                return nth_variation(translation_choices, n_variation, translations)
            else:
                for transition in reversed(first_choice.transitions):
                    if trie.transition_has_key(transition, TRIE_STROKE_BOUNDARY_KEY): break
                    if not trie.transition_has_key(transition, banks_info.positionless.rtfcre): continue

                    return nth_variation(translation_choices, n_variation, translations)

            return nth_variation(translation_choices, n_variation + 1, translations) if len(translation_choices) > 1 else None


        def nth_variation(choices: list[LookupResult[int]], n_variation: int, translations: list[str]):
            # index = n_variation % (len(choices) + 1)
            # return choices[index][0] if index != len(choices) else None
            return translations[choices[n_variation % len(choices)].translation]


        return None

    return plugin


def _join_all_translations(trie: NondeterministicTrie[str, int], results: Iterable[LookupResult[int]], translations: list[str]):
    return "\n".join(_summarize_result(trie, result, translations) for result in results)

def _summarize_result(trie: NondeterministicTrie[str, int], result: LookupResult[int], translations: list[str]):
    return f"""{translations[result.translation]} [#{result.translation}] ({result.cost})
    {_summarize_transitions(trie, result.transitions, result.translation)}"""

def _summarize_transitions(trie: NondeterministicTrie[str, int], transitions: Iterable[TransitionKey], entry_id: int):
    try:
        return f"{''.join(_summarize_transition(trie, transition, entry_id) for transition in transitions)}→"
    except KeyError as e:
        return f"bad transitions: {str(e)}"

def _summarize_transition(trie: NondeterministicTrie[str, int], transition: TransitionKey, entry_id: int):
    cost = trie.get_transition_cost(transition, entry_id)

    return f"—[{trie.get_key_str(transition.key_id)} ({cost})]"
    
