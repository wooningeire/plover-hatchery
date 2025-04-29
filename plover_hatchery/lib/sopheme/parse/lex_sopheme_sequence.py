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
        if self.__state is not TokenType.SYMBOL and self.__state == target_state:
            self.__state = target_state
            self.__current_token += char

            return


        if self.__state is not TokenType.START:
            yield Token(self.__state, self.__current_token)

        self.__state = target_state
        self.__current_token = char

    def step_eol(self):
        return Token(self.__state, self.__current_token)


def lex_sopheme_sequence(seq: str):
    lexer = _Lexer()

    tokens: list[Token] = []

    for char in seq:
        if char == " ":
            tokens.extend(lexer.step(char, TokenType.WHITESPACE))
        elif char.isalnum() or char in "-@#^':":
            tokens.extend(lexer.step(char, TokenType.CHARS))
        else:
            tokens.extend(lexer.step(char, TokenType.SYMBOL))
    
    tokens.append(lexer.step_eol())

    return tuple(tokens)