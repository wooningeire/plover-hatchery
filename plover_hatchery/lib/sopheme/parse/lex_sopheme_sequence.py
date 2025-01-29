from enum import Enum, auto
from typing import NamedTuple

class TokenType(Enum):
    START = auto()
    WHITESPACE = auto()
    CHARS = auto()
    SYMBOL = auto()

class Token(NamedTuple):
    type: TokenType
    value: str


class _Lexer:
    def __init__(self):
        self.__state = TokenType.START
        self.__current_token = ""

    def step(self, char: str, target_state: TokenType):
        if self.__state == target_state:
            self.__current_token += char
        else:
            if self.__state is not TokenType.START:
                yield Token(self.__state, self.__current_token)
            self.__current_token = char

        self.__state = target_state

    def step_eol(self):
        return Token(self.__state, self.__current_token)


def lex_sopheme_sequence(seq: str):
    lexer = _Lexer()

    for char in seq:
        if char == " ":
            yield from lexer.step(char, TokenType.WHITESPACE)
        elif char.isalnum() or char in "-/@":
            yield from lexer.step(char, TokenType.CHARS)
        else:
            yield from lexer.step(char, TokenType.SYMBOL)
    
    yield lexer.step_eol()