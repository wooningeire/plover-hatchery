from collections.abc import Callable
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.banks import banks
from plover_hatchery.lib.sopheme import Keysymbol, Sound


def optional_vowels() -> Plugin[None]:
    @define_plugin(optional_vowels)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_api = get_plugin_api(banks)


        @banks_api.begin_vowel.listen(optional_vowels)
        def _(vowel: Sound, set_vowel: Callable[[Sound], None], **_):
            new_keysymbol = Keysymbol(vowel.keysymbol.symbol, vowel.keysymbol.stress, True)
            set_vowel(Sound(new_keysymbol, vowel.sopheme))


        return None

    
    return plugin