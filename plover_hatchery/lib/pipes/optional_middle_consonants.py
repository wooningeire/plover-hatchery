from collections.abc import Callable
import dataclasses
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.banks import BanksState, banks
from plover_hatchery.lib.sopheme import Keysymbol, Sound


def optional_middle_consonants(
    *,
    ignore_consonant_if: Callable[[Sound], bool],
) -> Plugin[None]:
    @define_plugin(optional_middle_consonants)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_api = get_plugin_api(banks)


        @banks_api.begin_consonant.listen(optional_middle_consonants)
        def _(banks_state: BanksState, consonant: Sound, set_consonant: Callable[[Sound], None], **_):
            # Filter out starting and ending consonants
            if banks_state.group_index == 0 or banks_state.sounds.is_last_group(banks_state.group_index):
                return

            # Custom condition
            if not ignore_consonant_if(consonant):
                return

            set_consonant(dataclasses.replace(consonant, keysymbol=dataclasses.replace(consonant.keysymbol, optional=True)))


        return None

    
    return plugin