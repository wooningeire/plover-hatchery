
from collections.abc import Iterable
from plover.steno import Stroke

from plover_hatchery.lib.config import TRIE_STROKE_BOUNDARY_KEY
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.declare_banks import declare_banks
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, Transition


def splitter_lookup(*, cycler: "str | None"=None, prohibit_strokes: Iterable[str]=()) -> Plugin[None]:
    cycler_stroke = Stroke.from_steno(cycler) if cycler is not None else None
    prohibited_strokes = tuple(Stroke.from_steno(steno) for steno in prohibit_strokes)


    @define_plugin(splitter_lookup)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_) -> None:
        banks_info = get_plugin_api(declare_banks)


        @base_hooks.lookup.listen(splitter_lookup)
        def _(trie: NondeterministicTrie[str, int], stroke_stenos: tuple[str, ...], translations: list[str], **_) -> "str | None":
            # plover.log.debug("")
            # plover.log.debug("new lookup")

            current_nodes = {
                trie.ROOT: (),
            }
            n_variation = 0

            asterisk = Stroke.from_integer(0)

            for i, stroke_steno in enumerate(stroke_stenos):
                stroke = Stroke.from_steno(stroke_steno)
                if len(stroke) == 0:
                    return None
                
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

                if n_variation > 0:
                    return None
                
                if i > 0:
                    # plover.log.debug(current_nodes)
                    # plover.log.debug(TRIE_STROKE_BOUNDARY_KEY)
                    current_nodes = trie.get_dst_nodes(current_nodes, TRIE_STROKE_BOUNDARY_KEY)
                    if len(current_nodes) == 0:
                        return None

                left_bank_consonants, vowels, right_bank_consonants, asterisk = banks_info.split_stroke_parts(stroke)

                if len(left_bank_consonants) > 0:
                    # plover.log.debug(current_nodes)
                    # plover.log.debug(left_bank_consonants.keys())
                    if len(asterisk) > 0:
                        for key in left_bank_consonants.keys():
                            current_nodes = trie.get_dst_nodes(current_nodes, key)
                            # plover.log.debug(f"\t{key}\t {current_nodes}")
                            current_nodes |= trie.get_dst_nodes_chain(current_nodes, asterisk.keys())
                            # plover.log.debug(f"\t{asterisk.rtfcre}\t {current_nodes}")
                            if len(current_nodes) == 0:
                                return None
                    # elif left_bank_consonants == amphitheory.spec.LINKER_CHORD:
                    #     current_nodes = trie.get_dst_nodes_chain(current_nodes, left_bank_consonants.keys()) | trie.get_dst_nodes(current_nodes, TRIE_LINKER_KEY)
                    else:
                        current_nodes = trie.get_dst_nodes_chain(current_nodes, left_bank_consonants.keys())

                    if len(current_nodes) == 0:
                        return None

                if len(vowels) > 0:
                    # plover.log.debug(current_nodes)
                    # plover.log.debug(vowels.rtfcre)
                    if len(asterisk) > 0:
                        for key in vowels.keys():
                            current_nodes = trie.get_dst_nodes(current_nodes, key)
                            # plover.log.debug(f"\t{key}\t {current_nodes}")
                            current_nodes |= trie.get_dst_nodes_chain(current_nodes, asterisk.keys())
                            # plover.log.debug(f"\t{asterisk.rtfcre}\t {current_nodes}")
                            if len(current_nodes) == 0:
                                return None
                    else:
                        current_nodes = trie.get_dst_nodes_chain(current_nodes, vowels.keys())

                if len(right_bank_consonants) > 0:
                    # plover.log.debug(current_nodes)
                    # plover.log.debug(right_bank_consonants.keys())
                    if len(asterisk) > 0:
                        for key in right_bank_consonants.keys():
                            current_nodes |= trie.get_dst_nodes_chain(current_nodes, asterisk.keys())
                            # plover.log.debug(f"\t{asterisk.rtfcre}\t {current_nodes}")
                            current_nodes = trie.get_dst_nodes(current_nodes, key)
                            # plover.log.debug(f"\t{key}\t {current_nodes}")
                            if len(current_nodes) == 0:
                                return None
                    else:
                        current_nodes = trie.get_dst_nodes_chain(current_nodes, right_bank_consonants.keys())
                        
                    if len(current_nodes) == 0:
                        return None
                    
            translation_choices = sorted(trie.get_translations_and_costs(current_nodes), key=lambda result: result.cost)
            if len(translation_choices) == 0: return None

            first_choice = translation_choices[0]
            if len(asterisk) == 0:
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
