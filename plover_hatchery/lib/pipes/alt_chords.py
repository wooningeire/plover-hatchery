from collections.abc import Iterable

from plover.steno import Stroke

from plover_hatchery.lib.pipes.Plugin import Plugin, define_plugin, GetPluginApi
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.pipes.plugin_utils import join_sophs_to_chords_dicts
from plover_hatchery.lib.pipes.soph_trie import LookupResultWithAssociations, SophChordAssociation, soph_trie


def alt_chords(
    *,
    sophs_to_alternate_chords_dicts: Iterable[dict[str, str]],
    sophs_to_main_chords_dicts: Iterable[dict[str, str]],
) -> Plugin[None]:
    """Declares given chords as alternate chords, or chords that are only available when the typical "main" chord cannot be used.
    
    Example: `KOFT` ↦ cost. `-F` is an alt chord for S. It is available because the main chord `-S` could not be used in this stroke, since it comes after `-T`.
    """

    sophs_to_alternate_chords = join_sophs_to_chords_dicts(sophs_to_alternate_chords_dicts)
    sophs_to_main_chords = join_sophs_to_chords_dicts(sophs_to_main_chords_dicts, set)


    @define_plugin(alt_chords)
    def plugin(get_plugin_api: GetPluginApi, **_):
        soph_trie_api = get_plugin_api(soph_trie)
        floating_keys_api = get_plugin_api(floating_keys)


        @soph_trie_api.validate_lookup_result.listen(alt_chords)
        def _(result: LookupResultWithAssociations, **_):
            # Return true iff, for every alt chord path taken, all of the main chords were unusable

            for i, (sophs, chord, begins_new_stroke, phonemes, transitions) in enumerate(result.sophs_and_chords_used):
                if sophs not in sophs_to_alternate_chords: continue
                if chord not in sophs_to_alternate_chords[sophs]: continue


                if i == 0 or begins_new_stroke:
                    preceding_chord = Stroke.from_integer(0)
                else:
                    preceding_chord = result.sophs_and_chords_used[i - 1].chord

                if i == len(result.sophs_and_chords_used) - 1 or result.sophs_and_chords_used[i + 1].chord_starts_new_stroke:
                    following_chord = Stroke.from_integer(0)
                else:
                    following_chord = result.sophs_and_chords_used[i + 1].chord


                for main_chord in sophs_to_main_chords.get(sophs, ()):
                    if not floating_keys_api.can_add_stroke_on(preceding_chord, main_chord):
                        continue
                    if not floating_keys_api.can_add_stroke_on(main_chord, following_chord):
                        continue

                    return False
                
            return True


        return None


    return plugin