from collections.abc import Callable
import dataclasses
from typing import Any, Protocol
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.sopheme import Sopheme, DefinitionSophemes, DefinitionCursor

from plover_hatchery_lib_rs import Def, DefView, DefViewCursor, DefViewItem, Entity, Keysymbol, RawableEntity

class BaseOptionalizePredicate(Protocol):
    def __call__(self, cursor: DefViewCursor, /) -> bool: ...

class InjectedOptionalizePredicate(Protocol):
    def __call__(self, optionalize_if: BaseOptionalizePredicate, cursor: DefViewCursor, /) -> bool: ...


def create_optionalizer_with_user_condition(
    *,
    should_optionalize: InjectedOptionalizePredicate,
):
    def optionalizer_plugin(
        *,
        make_optional_if: BaseOptionalizePredicate,
    ) -> Plugin[None]:
        @define_plugin(optionalizer_plugin)
        def plugin(base_hooks: TheoryHooks, **_):
            @base_hooks.process_def.listen(optionalizer_plugin)
            def _(view: DefView, **_):
                return Def([], "")

                # def map_sopheme(cursor: ):
                #     keysymbols: list[Keysymbol] = []

                #     for phoneme in keysymbols:
                #         if should_optionalize(make_optional_if, phoneme):
                #             keysymbols.append(Keysymbol(phoneme.keysymbol.symbol, phoneme.keysymbol.stress, True))
                #         else:
                #             keysymbols.append(phoneme.keysymbol)

                #     yield Sopheme(sopheme.chars, list(keysymbols))

                # def map_def(cursor: DefViewCursor):
                #     if (item := cursor.tip()) is None or (definition := item.maybe_def) is None:
                #         raise Exception

                #     new_def = Def([], )

                    
                #     return new_def

                # def map_item(cursor: DefViewCursor):
                #     if (item := cursor.tip()) is None:
                #         raise Exception

                #     if item.is_def:
                #         new_def.rawables.append(RawableEntity.RawDef(map_def(cursor)))

                #     elif item.is_sopheme:
                #         if (sopheme := entity.maybe_sopheme) is not None:
                #             new_def.rawables.append(RawableEntity.Entity(Entity.Sopheme(map_sopheme(sopheme))))
                #         elif (transclusion := entity.maybe_transclusion) is not None:
                #             new_def.rawables.append(RawableEntity.Entity(Entity.Transclusion(entity)))

                
                # return view.map(map_def)


                # for sopheme, phonemes in view.phonemes_by_sopheme():
                #     keysymbols: list[Keysymbol] = []

                #     for phoneme in phonemes:
                #         if should_optionalize(make_optional_if, phoneme):
                #             keysymbols.append(Keysymbol(phoneme.keysymbol.symbol, phoneme.keysymbol.stress, True))
                #         else:
                #             keysymbols.append(phoneme.keysymbol)

                #     yield Sopheme(sopheme.chars, list(keysymbols))


            return None

        
        return plugin
    

    return optionalizer_plugin


def create_optionalizer(
    *,
    should_optionalize: BaseOptionalizePredicate,
):
    def optionalizer_plugin() -> Plugin[None]:
        @define_plugin(optionalizer_plugin)
        def plugin(base_hooks: TheoryHooks, **_):
            @base_hooks.process_def.listen(optionalizer_plugin)
            def _(view: DefView, **_):
                return Def([], "")

                # for sopheme, phonemes in sopheme_seq.phonemes_by_sopheme():
                #     keysymbols: list[Keysymbol] = []

                #     for phoneme in phonemes:
                #         if should_optionalize(phoneme):
                #             keysymbols.append(Keysymbol(phoneme.keysymbol.symbol, phoneme.keysymbol.stress, True))
                #         else:
                #             keysymbols.append(phoneme.keysymbol)

                #     yield Sopheme(sopheme.chars, list(keysymbols))


            return None

        
        return plugin
    

    return optionalizer_plugin