from collections.abc import Callable, Iterable

from plover.steno import Stroke

from ..trie import NondeterministicTrie
from ..config import TRIE_STROKE_BOUNDARY_KEY

from .Plugin import Plugin, GetPluginApi, define_plugin
from .declare_banks import declare_banks
from .compile_theory import TheoryHooks


def path_traversal_reverse_lookup() -> Plugin[None]:
    @define_plugin(path_traversal_reverse_lookup)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        banks_info = get_plugin_api(declare_banks)


        reverse_lookups: dict[int, Callable[[str], Iterable[tuple[str, ...]]]] = {}


        @base_hooks.reverse_lookup.listen(path_traversal_reverse_lookup)
        def _(trie: NondeterministicTrie[str, str], translation: str) -> Iterable[tuple[str, ...]]:
            if id(trie) in reverse_lookups:
                reverse_lookup = reverse_lookups[id(trie)]
            else:
                reverse_lookup = trie.build_reverse_lookup()
                reverse_lookups[id(trie)] = reverse_lookup

            
            for seq in reverse_lookup(translation):
                outline: list[str] = []
                latest_stroke: Stroke = Stroke.from_integer(0)
                invalid = False
                for key in seq:
                    if key == TRIE_STROKE_BOUNDARY_KEY:
                        outline.append(latest_stroke.rtfcre)
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

                if not invalid:
                    outline.append(latest_stroke.rtfcre)
                    yield tuple(outline)


        return None


    return plugin