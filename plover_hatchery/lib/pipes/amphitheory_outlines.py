from dataclasses import dataclass
from plover.steno import Stroke
from plover_hatchery.lib.pipes import soph_trie
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin


def amphitheory_outlines() -> Plugin[None]:
    linker_chord = Stroke.from_steno("^")
    capital_chord = Stroke.from_steno("#")

    modifiers_stroke = linker_chord + capital_chord

    @define_plugin(amphitheory_outlines)
    def plugin(get_plugin_api: GetPluginApi, **_):
        soph_trie_api = get_plugin_api(soph_trie)


        @dataclass
        class AmphitheoryOutlinesState:
            link: bool = False
            capital: bool = False


        @soph_trie_api.begin_lookup.listen(amphitheory_outlines)
        def _(**_):
            return AmphitheoryOutlinesState()


        @soph_trie_api.process_outline.listen(amphitheory_outlines)
        def _(state: AmphitheoryOutlinesState, outline: tuple[Stroke, ...], **_):
            # The empty outline is not allowed
            if len(outline) == 0:
                return None
            

            for i, stroke in enumerate(outline):
                # Strokes that are only modifiers are not allowed
                if stroke in modifiers_stroke:
                    return None

                # All strokes after the first must contain the linker chord
                if i == 0: continue

                if linker_chord not in stroke:
                    return None

            
            if linker_chord in outline[0]:
                state.link = True

            if capital_chord in outline[0]:
                state.capital = True
                

            return tuple(stroke - linker_chord - capital_chord for stroke in outline)


        @soph_trie_api.modify_translation.listen(amphitheory_outlines)
        def _(state: AmphitheoryOutlinesState, translation: str, **_):
            if state.link and state.capital:
                return "{^~|}" + translation

            elif state.link:
                return "{^}" + translation
            
            elif state.capital:
                return "{~|}" + translation
            
            return translation


        return None

    return plugin