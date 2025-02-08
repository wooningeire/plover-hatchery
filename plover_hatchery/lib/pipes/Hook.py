from typing import TypeVar, Generic, Callable, Any, cast


T = TypeVar("T", bound=Callable)

class Hook(Generic[T]):
    """A collection of event listeners"""
    def __init__(self):
        self.__handlers: dict[int, T] = {}
    
    def listen(self, plugin_id: int):
        def add_handler(handler: T):
            self.__handlers[plugin_id] = handler

        return add_handler

    def handlers(self):
        return self.__handlers.values()
    
    def ids_handlers(self):
        return self.__handlers.items()


class HookAttr(Generic[T]):
    def __init__(self, handler_protocol: type[T]):
        self.__private_attr_name: str

    def __set_name__(self, owner_class: type, attr_name: str):
        self.__private_attr_name = f"__{owner_class.__name__}_{attr_name}"

    def __get__(self, instance: Any, owner_class: type) -> Hook[T]:
        if not hasattr(instance, self.__private_attr_name):
            setattr(instance, self.__private_attr_name, Hook())
        return cast(Hook[T], getattr(instance, self.__private_attr_name))
    
    def __set__(self, instance: Any, value: T):
        if hasattr(instance, self.__private_attr_name): return
        setattr(instance, self.__private_attr_name, Hook())