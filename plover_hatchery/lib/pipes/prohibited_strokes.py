from typing import Any

from plover.steno import Stroke
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.theory_symbol_trie import theory_symbol_trie


def prohibited_strokes(stenos: str) -> Plugin[None]:
    strokes = set(Stroke.from_steno(steno) for steno in stenos)

    @define_plugin(prohibited_strokes)
    def plugin(get_plugin_api: GetPluginApi, **_):
        theory_symbol_trie_api = get_plugin_api(theory_symbol_trie)


        @theory_symbol_trie_api.process_outline.listen(theory_symbol_trie)
        def _(outline: tuple[Stroke, ...], **_):
            for stroke in outline:
                if stroke in strokes:
                    return None
            
            return outline


        return None

    return plugin