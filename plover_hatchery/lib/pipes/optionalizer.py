from collections.abc import Callable
import dataclasses
from typing import Protocol
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.sopheme import Keysymbol, Sopheme, SophemeSeq, SophemeSeqPhoneme


class BaseOptionalizePredicate(Protocol):
    def __call__(self, phoneme: SophemeSeqPhoneme, /) -> bool: ...

class InjectedOptionalizePredicate(Protocol):
    def __call__(self, optionalize_if: BaseOptionalizePredicate, phoneme: SophemeSeqPhoneme, /) -> bool: ...


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
            @base_hooks.process_sopheme_seq.listen(optionalizer_plugin)
            def _(sopheme_seq: SophemeSeq, **_):
                for sopheme, phonemes in sopheme_seq.phonemes_by_sopheme():
                    keysymbols: list[Keysymbol] = []

                    for phoneme in phonemes:
                        if should_optionalize(make_optional_if, phoneme):
                            keysymbols.append(dataclasses.replace(phoneme.keysymbol, optional=True))
                        else:
                            keysymbols.append(phoneme.keysymbol)

                    yield Sopheme(sopheme.chars, tuple(keysymbols))


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
            @base_hooks.process_sopheme_seq.listen(optionalizer_plugin)
            def _(sopheme_seq: SophemeSeq, **_):
                for sopheme, phonemes in sopheme_seq.phonemes_by_sopheme():
                    keysymbols: list[Keysymbol] = []

                    for phoneme in phonemes:
                        if should_optionalize(phoneme):
                            keysymbols.append(dataclasses.replace(phoneme.keysymbol, optional=True))
                        else:
                            keysymbols.append(phoneme.keysymbol)

                    yield Sopheme(sopheme.chars, tuple(keysymbols))


            return None

        
        return plugin
    

    return optionalizer_plugin