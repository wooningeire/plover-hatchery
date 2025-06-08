from typing import Callable
from collections.abc import Iterable

from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery_lib_rs import Def, DefView, DefViewCursor, Keysymbol, add_diphthong_keysymbols

from ..sopheme import Sopheme
from .Plugin import GetPluginApi, Plugin, define_plugin

    # class _OutlineSoundsBuilder:
    #     def __init__(self):
    #         self.__consonant_vowel_groups: list[ConsonantVowelGroup] = []
    #         self.__current_group_consonants: list[Sound] = []


    #     @property
    #     def __last_sound_was_vowel(self):
    #         return len(self.__consonant_vowel_groups) > 0 and len(self.__current_group_consonants) == 0


    #     def __append_diphthong_transition(self):
    #         if not self.__last_sound_was_vowel: return
            
    #         prev_vowel = self.__consonant_vowel_groups[-1].vowel
    #         diphthong_transition_sophemes = vowel_diphthong_transition(prev_vowel)
    #         for sopheme in diphthong_transition_sophemes:
    #             self.__current_group_consonants.append(Sound(sopheme.keysymbols[0], sopheme))
    #             break
    #             # TODO


    #     def add_consonant(self, consonant: SophemeSeqEntry):
    #         self.__current_group_consonants.append(consonant)
        

    #     def add_vowel(self, vowel: SophemeSeqEntry):
    #         self.__append_diphthong_transition()

    #         self.__consonant_vowel_groups.append(ConsonantVowelGroup(tuple(self.__current_group_consonants), vowel))
    #         self.__current_group_consonants = []


    #     def build_sounds(self):
    #         return OutlineSounds(tuple(self.__consonant_vowel_groups), tuple(self.__current_group_consonants))


    # def get_sopheme_sounds(sophemes: Iterable[Sopheme]):
    #     builder = _OutlineSoundsBuilder()

    #     for sopheme in sophemes:
    #         for keysymbol in sopheme.keysymbols:
    #             if keysymbol.is_vowel:
    #                 builder.add_vowel(Sound(keysymbol, sopheme))
    #             else:
    #                 builder.add_consonant(Sound(keysymbol, sopheme))


    #     return builder.build_sounds()

def diphthong_transition_consonants(
    *,
    keysymbols_by_first_vowel: Callable[[DefViewCursor], Iterable[Keysymbol]],
) -> Plugin[None]:
    @define_plugin(diphthong_transition_consonants)
    def plugin(base_hooks: TheoryHooks, **_):
        @base_hooks.process_def.listen(diphthong_transition_consonants)
        def _(view: DefView, **_):
            last_keysymbol_cur_if_vowel = None

            def map_keysymbols(cur: DefViewCursor):
                nonlocal last_keysymbol_cur_if_vowel

                keysymbol = cur.tip().keysymbol()
                if last_keysymbol_cur_if_vowel is not None:
                    keysymbols = tuple(keysymbols_by_first_vowel(last_keysymbol_cur_if_vowel))
                else:
                    keysymbols = ()


                if keysymbol.is_vowel:
                    last_keysymbol_cur_if_vowel = cur
                else:
                    last_keysymbol_cur_if_vowel = None


                return keysymbols

            
            return add_diphthong_keysymbols(view, map_keysymbols)

        return None

    
    return plugin