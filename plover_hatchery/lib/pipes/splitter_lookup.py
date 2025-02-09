
from collections.abc import Iterable
from plover.steno import Stroke

from plover_hatchery.lib.config import TRIE_STROKE_BOUNDARY_KEY
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.declare_banks import declare_banks
from plover_hatchery.lib.trie import NondeterministicTrie, Transition, TrieIndex, TrieIndexLookupResult


def splitter_lookup(*, cycler: "str | None"=None, prohibit_strokes: Iterable[str]=()) -> Plugin[None]:
    cycler_stroke = Stroke.from_steno(cycler) if cycler is not None else None
    prohibited_strokes = tuple(Stroke.from_steno(steno) for steno in prohibit_strokes)


    @define_plugin(splitter_lookup)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_) -> None:
        banks_info = get_plugin_api(declare_banks)


        @base_hooks.lookup.listen(splitter_lookup)
        def _(tries: TrieIndex, stroke_stenos: tuple[str, ...], **_) -> "str | None":
            # plover.log.debug("")
            # plover.log.debug("new lookup")

            lookup = tries.create_lookup()
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
                    lookup.traverse(TRIE_STROKE_BOUNDARY_KEY)

                left_bank_consonants, vowels, right_bank_consonants, asterisk = banks_info.split_stroke_parts(stroke)

                if len(left_bank_consonants) > 0:
                    # plover.log.debug(current_nodes)
                    # plover.log.debug(left_bank_consonants.keys())
                    if len(asterisk) > 0:
                        for key in left_bank_consonants.keys():
                            lookup.traverse(key, asterisk.keys())
                            # plover.log.debug(f"\t{key}\t {current_nodes}")
                            # plover.log.debug(f"\t{asterisk.rtfcre}\t {current_nodes}")

                    # elif left_bank_consonants == amphitheory.spec.LINKER_CHORD:
                    #     current_nodes = trie.get_dst_nodes_chain(current_nodes, left_bank_consonants.keys()) | trie.get_dst_nodes(current_nodes, TRIE_LINKER_KEY)
                    else:
                        lookup.traverse(left_bank_consonants.keys())

                if len(vowels) > 0:
                    # plover.log.debug(current_nodes)
                    # plover.log.debug(vowels.rtfcre)
                    if len(asterisk) > 0:
                        for key in vowels.keys():
                            lookup.traverse(key, asterisk.keys())
                            # plover.log.debug(f"\t{key}\t {current_nodes}")
                            # plover.log.debug(f"\t{asterisk.rtfcre}\t {current_nodes}")
                    else:
                        current_nodes = lookup.traverse(vowels.keys())

                if len(right_bank_consonants) > 0:
                    # plover.log.debug(current_nodes)
                    # plover.log.debug(right_bank_consonants.keys())
                    if len(asterisk) > 0:
                        for key in right_bank_consonants.keys():
                            lookup.traverse(asterisk.keys(), key)
                            # plover.log.debug(f"\t{asterisk.rtfcre}\t {current_nodes}")
                            # plover.log.debug(f"\t{key}\t {current_nodes}")
                    else:
                        lookup.traverse(right_bank_consonants.keys())
                    
            translation_choices = sorted(lookup.get_translations().items(), key=lambda cost_info: cost_info[1].cost)
            if len(translation_choices) == 0: return None

            first_choice = translation_choices[0]
            if len(asterisk) == 0:
                return nth_variation(translation_choices, n_variation)
            else:
                trie = first_choice[1].trie
                for transition in reversed(first_choice[1].transitions):
                    if trie.transition_has_key(transition, TRIE_STROKE_BOUNDARY_KEY): break
                    if not trie.transition_has_key(transition, banks_info.positionless.rtfcre): continue

                    return nth_variation(translation_choices, n_variation)

            return nth_variation(translation_choices, n_variation + 1) if len(translation_choices) > 1 else None


        def nth_variation(choices: list[tuple[str, TrieIndexLookupResult]], n_variation: int):
            # index = n_variation % (len(choices) + 1)
            # return choices[index][0] if index != len(choices) else None
            return choices[n_variation % len(choices)][0]


        return None

    return plugin
