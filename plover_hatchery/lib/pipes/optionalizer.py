from collections.abc import Callable
import dataclasses
from typing import Any, Protocol
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.sopheme import Sopheme, DefinitionSophemes, DefinitionCursor

from plover_hatchery_lib_rs import Def, DefView, DefViewCursor, DefViewItem, Entity, Keysymbol, RawableEntity, optionalize_keysymbols

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
                return optionalize_keysymbols(view, lambda cursor: should_optionalize(make_optional_if, cursor))


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
                return optionalize_keysymbols(view, should_optionalize)

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