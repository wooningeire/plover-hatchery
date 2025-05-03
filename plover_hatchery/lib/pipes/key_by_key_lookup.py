
from collections import defaultdict
from collections.abc import Iterable
from typing import Protocol, final

from plover.steno import Stroke

from plover_hatchery.lib.trie.NondeterministicTrie import NondeterministicTrie
from plover_hatchery.lib.trie.TriePath import TriePath
from plover_hatchery.lib.config import TRIE_STROKE_BOUNDARY_KEY
from plover_hatchery.lib.pipes.Hook import Hook
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.declare_banks import declare_banks
from plover_hatchery.lib.pipes.lookup_result_filtering import lookup_result_filtering
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, TransitionKey, TriePath


@final
class KeyByKeyLookupApi:
    class CheckTraverse(Protocol):
        def __call__(
            self,
            *,
            trie: NondeterministicTrie[str, int],
            existing_trie_path: TriePath,
            new_transition: TransitionKey,
        ) -> bool: ...

    check_traverse = Hook(CheckTraverse)


def key_by_key_lookup(
    *,
    cycle_on: "str | None"=None,
    debug_on: "str | None"="",
    prohibit_strokes: Iterable[str]=(),
) -> Plugin[KeyByKeyLookupApi]:
    cycler_stroke = Stroke.from_steno(cycle_on) if cycle_on is not None else None
    debug_stroke = Stroke.from_steno(debug_on) if debug_on is not None else None

    prohibited_strokes = tuple(Stroke.from_steno(steno) for steno in prohibit_strokes)


    @define_plugin(key_by_key_lookup)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        banks_info = get_plugin_api(declare_banks)
        filtering_api = get_plugin_api(lookup_result_filtering)


        hooks = KeyByKeyLookupApi()

        
        def traverse_handler(trie: NondeterministicTrie[str, int], existing_trie_path: TriePath, new_transition: TransitionKey):
            return all(
                handler(
                    trie=trie,
                    existing_trie_path=existing_trie_path,
                    new_transition=new_transition,
                )
                for handler in hooks.check_traverse.handlers()
            )


        @base_hooks.build_lookup.listen(key_by_key_lookup)
        def _(trie: NondeterministicTrie[str, int], **_):
            trie.on_check_traverse(traverse_handler)


        @base_hooks.lookup.listen(key_by_key_lookup)
        def _(trie: NondeterministicTrie[str, int], stroke_stenos: tuple[str, ...], translations: list[str], **_) -> "str | None":
            # print()

            current_nodes = [TriePath(trie.ROOT, ())]
            n_variation = 0
            debug = False

            positionless = Stroke.from_integer(0)

            outline = tuple(Stroke.from_steno(steno) for steno in stroke_stenos)
            filtering_end_index = len(outline)
            for i, stroke in enumerate(outline):
                if len(stroke) == 0:
                    return None

                # The debug stroke must be the last stroke of the outline if present
                if debug_stroke is not None and i == len(stroke_stenos) - 1 and stroke == debug_stroke:
                    filtering_end_index = min(filtering_end_index, i)
                    debug = True
                    break
                
                # Increase the variation number for each cycler stroke
                if cycler_stroke is not None and stroke == cycler_stroke:
                    filtering_end_index = min(filtering_end_index, i)
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
                    current_nodes = list(trie.traverse(current_nodes, TRIE_STROKE_BOUNDARY_KEY))
                    # print(TRIE_STROKE_BOUNDARY_KEY, tuple(node.dst_node_id for node in current_nodes))
                    if len(current_nodes) == 0:
                        return None

                left_bank_consonants, vowels, right_bank_consonants, positionless = banks_info.split_stroke_parts(stroke)


                for positionless_key in positionless.keys():
                    current_nodes.extend(trie.traverse_chain(current_nodes, positionless_key))
                    # print(positionless_key, tuple(node.dst_node_id for node in current_nodes))


                for key in (left_bank_consonants + vowels + right_bank_consonants).keys():
                    current_nodes = list(trie.traverse(current_nodes, key))
                    # print(key, tuple(node.dst_node_id for node in current_nodes))
                    for positionless_key in positionless.keys():
                        current_nodes.extend(trie.traverse_chain(current_nodes, positionless_key))
                        # print(positionless_key, tuple(node.dst_node_id for node in current_nodes))

                    if len(current_nodes) == 0:
                        return None

            lookup_results = tuple(trie.get_translations_and_costs(current_nodes))

            print("/".join(stroke.rtfcre for stroke in outline), "ended with", len(current_nodes), "nodes and", len(lookup_results), "results")

            validated_lookup_results: list[LookupResult[int]] = []
            outline_for_filtering = outline[:filtering_end_index]
            for lookup_result in lookup_results:
                # print(lookup_result.translation)
                if not filtering_api.should_keep(lookup_result, trie, outline_for_filtering):
                    continue

                validated_lookup_results.append(lookup_result)


            if len(validated_lookup_results) == 0: return None


            # filter duplicates
            min_costs: dict[int, float] = defaultdict(lambda: float("inf"))
            min_cost_results: dict[int, LookupResult[int]] = {}
            for result in validated_lookup_results:
                if result.cost >= min_costs[result.translation]: continue
                min_costs[result.translation] = result.cost
                min_cost_results[result.translation] = result


            translation_choices = sorted(min_cost_results.values(), key=lambda result: result.cost)

            
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


        return hooks


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
    
