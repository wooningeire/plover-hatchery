from collections.abc import Callable, Iterable

from plover.steno import Stroke

from plover_hatchery.lib.pipes.lookup_result_filter import lookup_result_filter
from plover_hatchery.lib.trie import LookupResult
from plover_hatchery.lib.trie.Transition import TransitionKey

from ..trie import NondeterministicTrie
from ..config import TRIE_STROKE_BOUNDARY_KEY

from .Plugin import Plugin, GetPluginApi, define_plugin
from .declare_banks import declare_banks
from .compile_theory import TheoryHooks


def path_traversal_reverse_lookup() -> Plugin[None]:
    @define_plugin(path_traversal_reverse_lookup)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        banks_info = get_plugin_api(declare_banks)
        filtering_api = get_plugin_api(lookup_result_filter)


        reverse_lookups: dict[int, Callable[[int], Iterable[LookupResult[int]]]] = {}


        @base_hooks.reverse_lookup.listen(path_traversal_reverse_lookup)
        def _(trie: NondeterministicTrie[str, int], translation: str, reverse_translations: dict[str, list[int]], **_) -> Iterable[tuple[str, ...]]:
            if id(trie) in reverse_lookups:
                reverse_lookup = reverse_lookups[id(trie)]
            else:
                reverse_lookup = trie.build_reverse_lookup()
                reverse_lookups[id(trie)] = reverse_lookup

            
            for entry_id in reverse_translations[translation]:
                for lookup_result in reverse_lookup(entry_id):
                    outline: list[Stroke] = []
                    latest_stroke: Stroke = Stroke.from_integer(0)
                    invalid = False
                    for transition in lookup_result.transitions:
                        if transition.key_id is None: continue
                        key = trie.get_key(transition.key_id)

                        if key == TRIE_STROKE_BOUNDARY_KEY:
                            outline.append(latest_stroke)
                            latest_stroke = Stroke.from_integer(0)
                            continue

                        # if key == TRIE_LINKER_KEY:
                        #     key_stroke = amphitheory.spec.LINKER_CHORD
                        # else: 
                        key_stroke = Stroke.from_steno(key)

                        if banks_info.can_add_stroke_on(latest_stroke, key_stroke):
                            latest_stroke += key_stroke
                        else:
                            invalid = True
                            break

                    if invalid:
                        continue


                    outline.append(latest_stroke)

                    if not filtering_api.should_keep(lookup_result, trie, tuple(outline)):
                        continue

                    yield tuple(stroke.rtfcre for stroke in outline)


        return None


    return plugin