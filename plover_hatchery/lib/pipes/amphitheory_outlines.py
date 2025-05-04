from plover.steno import Stroke
from plover_hatchery.lib.pipes import soph_trie
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin


def amphitheory_outlines() -> Plugin[None]:
    linker_chord = Stroke.from_steno("^")

    @define_plugin(amphitheory_outlines)
    def plugin(get_plugin_api: GetPluginApi, **_):
        soph_trie_api = get_plugin_api(soph_trie)


        @soph_trie_api.process_outline.listen(amphitheory_outlines)
        def _(outline: tuple[Stroke, ...], **_):
            for i, stroke in enumerate(outline):
                if i == 0: continue

                if linker_chord not in stroke:
                    return None

            return outline


        @soph_trie_api.process_outline.listen(amphitheory_outlines)
        def _(outline: tuple[Stroke, ...], **_):
            return tuple(stroke - linker_chord for stroke in outline)


        return None

    return plugin