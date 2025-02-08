from typing import Any, TypeVar, Generic, Protocol, Callable
from dataclasses import dataclass


T = TypeVar("T")
U = TypeVar("U")

class GetPluginApi(Protocol):
    def __call__(self, plugin_factory: "Callable[..., Plugin[T]]", /) -> T: ...

class PluginInitializer(Protocol[T, U]):
    def __call__(self, *, get_plugin_api: GetPluginApi, base_hooks: U) -> T: ...

@dataclass
class Plugin(Generic[T]):
    id: int
    initialize: PluginInitializer[T, Any]


def define_plugin(plugin_factory: Callable[..., Plugin[T]]):
    def create_plugin(initialize: PluginInitializer[T, Any]) -> Plugin[T]:
        return Plugin(id(plugin_factory), initialize)
    
    return create_plugin