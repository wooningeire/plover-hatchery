from typing import TypeVar, Generic, Protocol, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .consonants_vowels_enumeration import ConsonantsVowelsEnumerationHooks


T = TypeVar("T")
U = TypeVar("U")

class GetPlugin(Protocol[T]):
    def __call__(self, plugin: "Plugin[T]") -> "T | None": ...

class PluginInitializer(Protocol[T]):
    def __call__(self, *, get_plugin: GetPlugin[T], base_hooks: "ConsonantsVowelsEnumerationHooks") -> T: ...

@dataclass
class Plugin(Generic[T]):
    id: int
    initialize: PluginInitializer[T]

    @staticmethod
    def define(initialize: PluginInitializer[T]) -> "Plugin[T]":
        return Plugin(id(initialize), initialize)
    
