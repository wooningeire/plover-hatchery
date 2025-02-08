from typing import TypeVar, Generic, Protocol, Callable, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .consonants_vowels_enumeration import ConsonantsVowelsEnumerationHooks


T = TypeVar("T")
U = TypeVar("U")

class GetPluginApi(Protocol):
    def __call__(self, plugin_factory: "Callable[..., Plugin[T]]", /) -> "T": ...

class PluginInitializer(Protocol[T]):
    def __call__(self, *, get_plugin_api: GetPluginApi, base_hooks: "ConsonantsVowelsEnumerationHooks") -> T: ...

@dataclass
class Plugin(Generic[T]):
    id: int
    initialize: PluginInitializer[T]


def define_plugin(plugin_id: int):
    def create_plugin(initialize: PluginInitializer[T]) -> Plugin[T]:
        return Plugin(plugin_id, initialize)
    
    return create_plugin