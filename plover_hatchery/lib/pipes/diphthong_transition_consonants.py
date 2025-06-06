from typing import Callable
from collections.abc import Iterable

from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.sopheme import DefinitionSophemes, DefinitionCursor
from plover_hatchery_lib_rs import Def, DefView, DefViewCursor

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
    sophemes_by_first_vowel: Callable[[DefViewCursor], Iterable[Sopheme]],
) -> Plugin[None]:
    @define_plugin(diphthong_transition_consonants)
    def plugin(base_hooks: TheoryHooks, **_):
        @base_hooks.process_def.listen(diphthong_transition_consonants)
        def _(view: DefView, **_):
            return Def([], "")


            # prev_phoneme_if_was_vowel = None


            # entities: list[OverridableEntity] = []
            # any_changes = False


            # def process_def(cursor: DefCursorController):

            #     def process_sopheme(sopheme: Sopheme):
            #         nonlocal prev_phoneme_if_was_vowel, any_changes


            #         keysymbols: list[Keysymbol] = []

            #         for i, keysymbol in enumerate(sopheme.keysymbols):
            #             if keysymbol.is_vowel and prev_phoneme_if_was_vowel is not None:
            #                 # Add the diphthong transition consonant
            #                 diphthong_transition_sophemes = sophemes_by_first_vowel(prev_phoneme_if_was_vowel)
            #                 for diphthong_sopheme in diphthong_transition_sophemes:
            #                     any_changes = True

            #                     if i == 0:
            #                         entities.append(OverridableEntity.sopheme(Sopheme("", diphthong_sopheme.keysymbols)))
            #                     else:
            #                         keysymbols.extend(diphthong_sopheme.keysymbols)
                                    
            #                     break
            #                     # TODO multiple options
                            
            #             keysymbols.append(keysymbol)

            #             if keysymbol.is_vowel:
            #                 prev_phoneme_if_was_vowel = (sopheme, keysymbol)
            #             else:
            #                 prev_phoneme_if_was_vowel = None
                    
            #         entities.append(Sopheme(sopheme.chars, list(keysymbols)))
                    

            #         return any_changes


            #     def process_inner_def(cursor: )


            #     return Def(cursor.map_def_entities(process_sopheme, process_def), cursor.get_def_varname()), any_changes


            # return Def(items, view.base_def.varname)


        return None

    
    return plugin