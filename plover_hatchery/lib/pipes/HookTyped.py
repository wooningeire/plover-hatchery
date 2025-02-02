from typing import Callable, TypeVarTuple

T = TypeVarTuple("T")

class Hook[*T]:
    """A collection of event listeners"""

    def __init__(self):
        self.__handlers: list[Callable[[*T], None]] = []
    
    def listen(self, handler: Callable[[*T], None]):
        self.__handlers.append(handler)

    def emit(self, *args: *T):
        for handler in self.__handlers:
            handler(*args)