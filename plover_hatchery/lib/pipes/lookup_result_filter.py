from typing import Protocol, final

from plover.steno import Stroke

from plover_hatchery.lib.pipes.Hook import Hook
from plover_hatchery.lib.pipes.Plugin import Plugin, GetPluginApi, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie


@final
class LookupResultFilterApi:
    class CheckShouldKeep(Protocol):
        def __call__(self, *, lookup_result: LookupResult[int], trie: NondeterministicTrie[str, int], outline: tuple[Stroke, ...]) -> bool: ...
    
    check_should_keep = Hook(CheckShouldKeep)

    def should_keep(self, lookup_result: LookupResult[int], trie: NondeterministicTrie[str, int], outline: tuple[Stroke, ...]):
        for handler in self.check_should_keep.handlers():
            if not handler(lookup_result=lookup_result, trie=trie, outline=outline):
                return False
        
        return True


def lookup_result_filter() -> Plugin[LookupResultFilterApi]:
    """Provides a common interface between plugins for filtering lookup results."""

    @define_plugin(lookup_result_filter)
    def plugin(**_):
        api = LookupResultFilterApi()

        return api


    return plugin