from enum import Enum, auto
from typing import NamedTuple

from .Sopheme import Sopheme, Orthokeysymbol, Keysymbol
from ..stenophoneme import Stenophoneme


class _TokenType(Enum):
    START = auto()
    WHITESPACE = auto()
    CHARS = auto()
    SYMBOL = auto()

class _Token(NamedTuple):
    type: _TokenType
    value: str

class _Lexer:
    def __init__(self):
        self.__state = _TokenType.START
        self.__current_token = ""

    def step(self, char: str, target_state: _TokenType):
        if self.__state == target_state:
            self.__current_token += char
        else:
            if self.__state is not _TokenType.START:
                yield _Token(self.__state, self.__current_token)
            self.__current_token = char

        self.__state = target_state

    def step_eol(self):
        return _Token(self.__state, self.__current_token)


def _lex_seq(seq: str):
    lexer = _Lexer()

    for char in seq:
        if char == " ":
            yield from lexer.step(char, _TokenType.WHITESPACE)
        elif char.isalnum() or char in "-/@":
            yield from lexer.step(char, _TokenType.CHARS)
        else:
            yield from lexer.step(char, _TokenType.SYMBOL)
    
    yield lexer.step_eol()
    


class _ParserState(Enum):
    DONE_SOPHEME = auto()
    DONE_ORTHO = auto()
    DONE_DOT = auto()
    DONE_KEYSYMBOL_GROUP_START_MARKER = auto()
    DONE_KEYSYMBOL_CHARS = auto()
    DONE_KEYSYMBOL_STRESS_MARKER = auto()
    DONE_KEYSYMBOL_STRESS_VALUE = auto()
    DONE_KEYSYMBOL_OPTIONAL_MARKER = auto()
    DONE_KEYSYMBOL = auto()
    DONE_PHONO = auto()


class _Parser:
    def __init__(self):
        self.__state = _ParserState.DONE_SOPHEME

        self.__parentheses_level = 0

        self.__has_active_sopheme = False
        self.__current_sopheme_chars = ""
        self.__current_sopheme_keysymbols: list[Keysymbol] = []

        self.__has_active_keysymbol = False
        self.__current_keysymbol_chars = ""
        self.__current_keysymbol_stress = 0
        self.__current_keysymbol_optional = False


    def __complete_sopheme(self):
        assert self.__has_active_sopheme

        sopheme = Orthokeysymbol(tuple(self.__current_sopheme_keysymbols), self.__current_sopheme_chars)
        self.__current_sopheme_chars = ""
        self.__current_sopheme_keysymbols = []

        self.__has_active_sopheme = False

        return sopheme
    
    
    def __complete_keysymbol(self):
        assert self.__has_active_keysymbol

        keysymbol = Keysymbol(self.__current_keysymbol_chars, "", self.__current_keysymbol_stress, self.__current_keysymbol_optional)
        self.__current_sopheme_keysymbols.append(keysymbol)

        self.__has_active_keysymbol = False
        

    def consume(self, token: _Token):
        print(token, self.__state)

        match self.__state:
            case _ParserState.DONE_SOPHEME:
                self.__consume_start_sopheme(token)
            case _ParserState.DONE_ORTHO:
                yield from self.__consume_done_ortho(token)
            case _ParserState.DONE_DOT:
                yield from self.__consume_done_dot(token)
            case _ParserState.DONE_KEYSYMBOL_GROUP_START_MARKER:
                self.__consume_done_keysymbol_group_start_marker(token)
            case _ParserState.DONE_KEYSYMBOL_CHARS:
                self.__consume_done_keysymbol_chars(token)
            case _ParserState.DONE_KEYSYMBOL_STRESS_MARKER:
                self.__consume_done_keysymbol_stress_marker(token)
            case _ParserState.DONE_KEYSYMBOL_STRESS_VALUE:
                self.__consume_done_keysymbol_stress_value(token)
            case _ParserState.DONE_PHONO:
                self.__consume_done_phono(token)

                
    def __consume_start_sopheme(self, token: _Token):
        match token.type:
            case _TokenType.CHARS:
                self.__state = _ParserState.DONE_ORTHO
                self.__current_sopheme_chars = token.value
                self.__has_active_sopheme = True

            case _TokenType.SYMBOL:
                match token.value:
                    case ".":
                        self.__state = _ParserState.DONE_DOT
                        self.__has_active_sopheme = True
                    
                    case _:
                        raise ValueError()

            case _TokenType.WHITESPACE:
                ...

            case _:
                raise TypeError()
        
            
    def __consume_done_ortho(self, token: _Token):
        match token.type:
            case _TokenType.CHARS:
                self.__state = _ParserState.DONE_KEYSYMBOL_CHARS
                self.__current_keysymbol_chars = token.value

            case _TokenType.SYMBOL:
                match token.value:
                    case ".":
                        self.__state = _ParserState.DONE_DOT
                    
                    case _:
                        raise ValueError()

            case _TokenType.WHITESPACE:
                yield self.__complete_sopheme()

                self.__state = _ParserState.DONE_SOPHEME

            case _:
                raise TypeError()
            

    def __consume_done_dot(self, token: _Token):
        match token.type:
            case _TokenType.CHARS:
                self.__state = _ParserState.DONE_KEYSYMBOL_CHARS
                self.__current_keysymbol_chars = token.value
                self.__has_active_keysymbol = True

            case _TokenType.SYMBOL:
                match token.value:
                    case "(":
                        self.__state = _ParserState.DONE_KEYSYMBOL_GROUP_START_MARKER
                        self.__parentheses_level += 1
                    
                    case _:
                        raise ValueError()

            case _TokenType.WHITESPACE:
                yield self.__complete_sopheme()

                self.__state = _ParserState.DONE_SOPHEME

            case _:
                raise TypeError()
                    

    def __consume_done_keysymbol_group_start_marker(self, token: _Token):
        match token.type:
            case _TokenType.CHARS:
                self.__state = _ParserState.DONE_KEYSYMBOL_CHARS
                self.__current_keysymbol_chars = token.value
                self.__has_active_keysymbol = True

            case _TokenType.SYMBOL:
                match token.value:
                    case ")":
                        self.__complete_keysymbol()

                        self.__state = _ParserState.DONE_PHONO
                        self.__parentheses_level -= 1
                    
                    case _:
                        raise ValueError()
            
            case _TokenType.WHITESPACE:
                ...

            case _:
                raise TypeError()
                    

    def __consume_done_keysymbol_chars(self, token: _Token):
        match token.type:
            case _TokenType.SYMBOL:
                match token.value:
                    case "!":
                        self.__state = _ParserState.DONE_KEYSYMBOL_STRESS_MARKER

                    case ")":
                        self.__complete_keysymbol()

                        self.__state = _ParserState.DONE_PHONO
                        self.__parentheses_level -= 1
                    
                    case _:
                        raise ValueError()
            
            case _TokenType.WHITESPACE:
                self.__complete_keysymbol()

                self.__state = _ParserState.DONE_KEYSYMBOL

            case _:
                raise TypeError()
            

    def __consume_done_keysymbol_stress_marker(self, token: _Token):
        match token.type:
            case _TokenType.CHARS:
                self.__state = _ParserState.DONE_KEYSYMBOL_STRESS_VALUE
                self.__current_keysymbol_stress = int(token.value)
                assert 1 <= self.__current_keysymbol_stress <= 3
            
            case _:
                raise TypeError()
            
    def __consume_done_keysymbol_stress_value(self, token: _Token):
        match token.type:
            case _TokenType.SYMBOL:
                match token.value:
                    case "?":
                        self.__state = _ParserState.DONE_KEYSYMBOL_OPTIONAL_MARKER
                        self.__current_keysymbol_optional = True

                    case ")":
                        self.__complete_keysymbol()

                        self.__state = _ParserState.DONE_PHONO
                        self.__parentheses_level -= 1

            case _TokenType.WHITESPACE:
                self.__complete_keysymbol()
                
                self.__state = _ParserState.DONE_KEYSYMBOL

            case _:
                raise TypeError()
    
    def __consume_done_phono(self, token: _Token):
        match token.type:
            case _TokenType.WHITESPACE:
                yield self.__complete_sopheme()
                
                self.__state = _ParserState.DONE_SOPHEME

            case _:
                raise TypeError()
    
    def consume_eol(self):
        if self.__parentheses_level > 0:
            raise ValueError()
        
        if self.__has_active_keysymbol:
            self.__complete_keysymbol()
        
        if self.__has_active_sopheme:
            yield self.__complete_sopheme()



def parse_seq(seq: str):
    parser = _Parser()

    for token in _lex_seq(seq):
        yield from parser.consume(token)

    yield from parser.consume_eol()