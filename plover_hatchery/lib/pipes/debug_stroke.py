

from typing import Any


from collections.abc import Iterable
from dataclasses import dataclass
from plover.steno import Stroke

from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.soph_trie import LookupResultWithAssociations, SophChordAssociation, soph_trie
from plover_hatchery.lib.pipes.types import Soph
from plover_hatchery.lib.trie import NondeterministicTrie
from plover_hatchery.lib.trie.Transition import TransitionKey


def debug_stroke(steno: str) -> Plugin[None]:
    stroke = Stroke.from_steno(steno)

    @define_plugin(debug_stroke)
    def plugin(get_plugin_api: GetPluginApi, **_):
        soph_trie_api = get_plugin_api(soph_trie)


        @dataclass
        class DebugStrokeState:
            should_debug = False


        @soph_trie_api.begin_lookup.listen(debug_stroke)
        def _(**_):
            return DebugStrokeState()


        @soph_trie_api.process_outline.listen(debug_stroke)
        def _(state: DebugStrokeState, outline: tuple[Stroke, ...], **_):
            if outline[-1] == stroke:
                state.should_debug = True
                return outline[:-1]

            return outline


        def join_all_translations(trie: NondeterministicTrie, results: Iterable[LookupResultWithAssociations], translations: list[str]):
            return "\n".join(summarize_result(trie, result, translations) for result in results)

        def summarize_result(trie: NondeterministicTrie, result: LookupResultWithAssociations, translations: list[str]):
            return (
                f"{translations[result.lookup_result.translation_id]} [#{result.lookup_result.translation_id}] ({result.lookup_result.cost})\n"
                    + "╒ transitions\n"
                    + f"{summarize_transitions(trie, result, result.lookup_result.translation_id)}\n"
                    + "╒ associations\n"
                    + f"{summarize_associations(result)}\n"
            )

        def get_combiner(is_last: bool):
            if is_last:
                return  "└"

            return "├"

        def summarize_transitions(trie: NondeterministicTrie, result: LookupResultWithAssociations, entry_id: int):
            try:
                return "\n".join(
                    summarize_transition(trie, transition, entry_id, i == len(result.lookup_result.transitions) - 1)
                    for i, transition in enumerate(result.lookup_result.transitions)
                )
            except KeyError as e:
                return f"└\t!! bad transitions: {e}"

        def summarize_transition(trie: NondeterministicTrie, transition: TransitionKey, entry_id: int, is_last: bool):
            cost = trie.get_transition_cost(transition, entry_id)

            return f"{get_combiner(is_last)}\t{soph_trie_api.key_id_manager.get_key_str(transition.key_id)} ({cost})"

        def summarize_associations(result: LookupResultWithAssociations):
            return "\n".join(
                summarize_association(association, i == 0, i == len(result.sophs_and_chords_used) - 1)
                for i, association in enumerate(result.sophs_and_chords_used)
            )

        def summarize_association(association: SophChordAssociation, is_first: bool, is_last: bool):
            out = ""
            if association.chord_starts_new_stroke and not is_first:
                out += "│\t/\n"

            out += f"{get_combiner(is_last)}\t{association.chord.rtfcre}\t→ {', '.join(str(soph) for soph in association.sophs)}"
            return out

        
        @soph_trie_api.select_translation.listen(debug_stroke)
        def _(
            state: DebugStrokeState,
            trie: NondeterministicTrie,
            choices: list[LookupResultWithAssociations],
            translations: list[str],
            **_,
        ):
            if not state.should_debug: return None

            return join_all_translations(trie, choices, translations)


        return None


    return plugin