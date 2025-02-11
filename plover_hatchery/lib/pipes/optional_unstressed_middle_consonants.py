from collections.abc import Callable
import dataclasses
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.banks import BanksState, banks
from plover_hatchery.lib.sopheme import Keysymbol, Sound


def optional_unstressed_middle_consonants(
    *,
    ignore_consonant_if: Callable[[Sound], bool],
) -> Plugin[None]:
    @define_plugin(optional_unstressed_middle_consonants)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_api = get_plugin_api(banks)


        @banks_api.begin_consonant.listen(optional_unstressed_middle_consonants)
        def _(banks_state: BanksState, consonant: Sound, set_consonant: Callable[[Sound], None], **_):
            # Filter out consonants that are not alone
            if banks_state.sounds.n_consonants_in_group(banks_state.group_index) > 1:
                return

            # Filter out starting and ending consonants
            if banks_state.group_index == 0 or banks_state.sounds.is_last_group(banks_state.group_index):
                return

            # Filter out consonants that are surrounded by stressed vowels
            if (
                banks_state.sounds.get_vowel_of_group(banks_state.group_index - 1).keysymbol.stress != 0
                or banks_state.sounds.get_vowel_of_group(banks_state.group_index).keysymbol.stress != 0
            ):
                return

            # Custom condition
            if not ignore_consonant_if(consonant):
                return

            set_consonant(dataclasses.replace(consonant, keysymbol=dataclasses.replace(consonant.keysymbol, optional=True)))


        return None

    
    return plugin