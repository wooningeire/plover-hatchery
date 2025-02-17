from typing import Protocol, final

from plover_hatchery.lib.pipes.Hook import Hook
from plover_hatchery.lib.pipes.Plugin import Plugin, GetPluginApi, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie


@final
class LookupResultFilteringApi:
    class DetermineShouldKeep(Protocol):
        def __call__(self, *, lookup_result: LookupResult[int], trie: NondeterministicTrie[str, int]) -> bool: ...
    
    determine_should_keep = Hook(DetermineShouldKeep)

    def should_keep(self, lookup_result: LookupResult[int], trie: NondeterministicTrie[str, int]):
        for handler in self.determine_should_keep.handlers():
            if not handler(lookup_result=lookup_result, trie=trie):
                return False
        
        return True


def lookup_result_filtering() -> Plugin[LookupResultFilteringApi]:
    @define_plugin(lookup_result_filtering)
    def plugin(**_):
        api = LookupResultFilteringApi()

        return api


    return plugin