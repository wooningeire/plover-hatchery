from typing import Callable, Any, TYPE_CHECKING


if TYPE_CHECKING:
    from .HookTyped import Hook
else:
    class Hook:
        """A collection of event listeners"""

        def __init__(self):
            self.__handlers: list[Callable[Any, None]] = []
        
        def listen(self, handler: Callable[Any, None]):
            self.__handlers.append(handler)

        def emit(self, *args: Any):
            for handler in self.__handlers:
                handler(*args)