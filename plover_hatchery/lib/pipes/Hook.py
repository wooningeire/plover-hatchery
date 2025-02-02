from typing import Callable

class Hook:
    def __init__(self):
        self.__handlers: list[Callable[[], None]] = []
    
    def listen(self, handler: Callable[[], None]):
        self.__handlers.append(handler)

    def emit(self):
        for handler in self.__handlers:
            handler()