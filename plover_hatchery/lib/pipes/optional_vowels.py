from collections.abc import Callable
import dataclasses
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.banks import BanksState, banks
from plover_hatchery.lib.sopheme import Keysymbol, Sound


def optional_vowels() -> Plugin[None]:
    @define_plugin(optional_vowels)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_api = get_plugin_api(banks)


        @banks_api.begin_vowel.listen(optional_vowels)
        def _(banks_state: BanksState, vowel: Sound, set_vowel: Callable[[Sound], None], **_):
            # Filter out starting vowels
            if len(banks_state.sounds.nonfinals[0].consonants) == 0 and banks_state.group_index == 0:
                return

            # Filter out ending vowels
            if len(banks_state.sounds.final_consonants) == 0 and banks_state.group_index == len(banks_state.sounds.nonfinals) - 1:
                return

            set_vowel(dataclasses.replace(vowel, keysymbol=dataclasses.replace(vowel.keysymbol, optional=True)))


        return None

    
    return plugin