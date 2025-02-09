from enum import Enum, auto
from typing import Any, Generator
from plover_hatchery.lib.sopheme.Sopheme import Sopheme

from ..Sopheme import Sopheme
from ..Keysymbol import Keysymbol
from .lex_sopheme_sequence import Token, TokenType, lex_sopheme_sequence



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

        sopheme = Sopheme(self.__current_sopheme_chars, tuple(self.__current_sopheme_keysymbols))
        
        self.__has_active_sopheme = False
        self.__current_sopheme_chars = ""
        self.__current_sopheme_keysymbols = []

        return sopheme
    
    
    def __complete_keysymbol(self):
        assert self.__has_active_keysymbol

        keysymbol = Keysymbol(self.__current_keysymbol_chars, self.__current_keysymbol_stress, self.__current_keysymbol_optional)
        self.__current_sopheme_keysymbols.append(keysymbol)

        self.__has_active_keysymbol = False
        self.__current_keysymbol_chars = ""
        self.__current_keysymbol_stress = 0
        self.__current_keysymbol_optional = False

    
    def __complete_keysymbol_or_sopheme(self):
        self.__complete_keysymbol()

        if self.__parentheses_level > 0:
            self.__state = _ParserState.DONE_KEYSYMBOL
        else: 
            yield self.__complete_sopheme()

            self.__state = _ParserState.DONE_SOPHEME


    def __complete_keysymbol_group(self):
        assert self.__parentheses_level > 0

        self.__state = _ParserState.DONE_PHONO
        self.__parentheses_level -= 1
        

    def consume(self, token: Token):
        if self.__state is _ParserState.DONE_SOPHEME:
            self.__consume_done_sopheme(token)
        elif self.__state is _ParserState.DONE_ORTHO:
            yield from self.__consume_done_ortho(token)
        elif self.__state is _ParserState.DONE_DOT:
            yield from self.__consume_done_dot(token)
        elif self.__state is _ParserState.DONE_KEYSYMBOL_GROUP_START_MARKER:
            self.__consume_done_keysymbol_group_start_marker(token)
        elif self.__state is _ParserState.DONE_KEYSYMBOL_CHARS:
            yield from self.__consume_done_keysymbol_chars(token)
        elif self.__state is _ParserState.DONE_KEYSYMBOL_STRESS_MARKER:
            self.__consume_done_keysymbol_stress_marker(token)
        elif self.__state is _ParserState.DONE_KEYSYMBOL_STRESS_VALUE:
            yield from self.__consume_done_keysymbol_stress_value(token)
        elif self.__state is _ParserState.DONE_KEYSYMBOL_OPTIONAL_MARKER:
            yield from self.__consume_done_keysymbol_optional_marker(token)
        elif self.__state is _ParserState.DONE_KEYSYMBOL:
            self.__consume_done_keysymbol(token)
        elif self.__state is _ParserState.DONE_PHONO:
            yield from self.__consume_done_phono(token)
        else:
            raise TypeError()

                
    def __consume_done_sopheme(self, token: Token):
        if token.type is TokenType.CHARS:
            self.__state = _ParserState.DONE_ORTHO
            self.__current_sopheme_chars = token.value
            self.__has_active_sopheme = True

        elif token.type is TokenType.SYMBOL:
            if token.value == ".":
                self.__state = _ParserState.DONE_DOT

                self.__has_active_sopheme = True
            
            else:
                raise ValueError()


        elif token.type is TokenType.WHITESPACE:
            ...

        else:
            raise TypeError()

        
            
    def __consume_done_ortho(self, token: Token):
        if token.type is TokenType.SYMBOL:
            if token.value == ".":
                self.__state = _ParserState.DONE_DOT

            else:
                raise ValueError()

        elif token.type is TokenType.WHITESPACE:

            yield self.__complete_sopheme()

            self.__state = _ParserState.DONE_SOPHEME

        else:
            raise TypeError()
            


    def __consume_done_dot(self, token: Token):
        if token.type is TokenType.CHARS:
            self.__state = _ParserState.DONE_KEYSYMBOL_CHARS
            self.__current_keysymbol_chars = token.value
            self.__has_active_keysymbol = True

        elif token.type is TokenType.SYMBOL:
            if token.value == "(":
                self.__state = _ParserState.DONE_KEYSYMBOL_GROUP_START_MARKER
                self.__parentheses_level += 1
            
            else:
                raise ValueError()

        elif token.type is TokenType.WHITESPACE:
            yield self.__complete_sopheme()

            self.__state = _ParserState.DONE_SOPHEME

        else:
            raise TypeError()


    def __consume_done_keysymbol_group_start_marker(self, token: Token):
        if token.type is TokenType.CHARS:
            self.__state = _ParserState.DONE_KEYSYMBOL_CHARS
            self.__current_keysymbol_chars = token.value
            self.__has_active_keysymbol = True

        elif token.type is TokenType.SYMBOL:
            if token.value == ")":
                self.__complete_keysymbol_group()
            
            else:
                raise ValueError()
        
        elif token.type is TokenType.WHITESPACE:
            ...

        else:
            raise TypeError()
                

    def __consume_done_keysymbol_chars(self, token: Token):
        if token.type is TokenType.SYMBOL:
            if token.value == "!":
                self.__state = _ParserState.DONE_KEYSYMBOL_STRESS_MARKER

            elif token.value == "?":
                self.__state = _ParserState.DONE_KEYSYMBOL_OPTIONAL_MARKER
                self.__current_keysymbol_optional = True

            elif token.value == ")":
                self.__complete_keysymbol()
                self.__complete_keysymbol_group()
            
            else:
                raise ValueError()
        
        elif token.type is TokenType.WHITESPACE:
            yield from self.__complete_keysymbol_or_sopheme()

        else:
            raise TypeError()
        

    def __consume_done_keysymbol_stress_marker(self, token: Token):
        if token.type is TokenType.CHARS:
            self.__state = _ParserState.DONE_KEYSYMBOL_STRESS_VALUE
            self.__current_keysymbol_stress = int(token.value)
            assert 1 <= self.__current_keysymbol_stress <= 3
        
        else:
            raise TypeError()
        
    def __consume_done_keysymbol_stress_value(self, token: Token) -> Generator[Sopheme, None, None]:
        if token.type is TokenType.SYMBOL:
            if token.value == "?":
                self.__state = _ParserState.DONE_KEYSYMBOL_OPTIONAL_MARKER
                self.__current_keysymbol_optional = True

            elif token.value == ")":
                self.__complete_keysymbol()
                self.__complete_keysymbol_group()

        elif token.type is TokenType.WHITESPACE:
            yield from self.__complete_keysymbol_or_sopheme()

        else:
            raise TypeError()
    
    def __consume_done_keysymbol_optional_marker(self, token: Token) -> Generator[Sopheme, None, None]:
        if token.type is TokenType.SYMBOL:
            if token.value == ")":
                self.__complete_keysymbol()
                self.__complete_keysymbol_group()

        elif token.type is TokenType.WHITESPACE:
            yield from self.__complete_keysymbol_or_sopheme()

        else:
            raise TypeError()

    def __consume_done_keysymbol(self, token: Token):
        if token.type is TokenType.CHARS:
            self.__state = _ParserState.DONE_KEYSYMBOL_CHARS
            self.__current_keysymbol_chars = token.value
            self.__has_active_keysymbol = True

        elif token.type is TokenType.SYMBOL:
            if token.value == ")":
                self.__complete_keysymbol_group()
            
            else:
                raise ValueError()
        
        elif token.type is TokenType.WHITESPACE:
            ...

        else:
            raise TypeError()
        
    def __consume_done_phono(self, token: Token):
        if token.type is TokenType.WHITESPACE:
            yield self.__complete_sopheme()
            
            self.__state = _ParserState.DONE_SOPHEME

        else:
            raise TypeError()
    
    def consume_eol(self):
        if self.__parentheses_level > 0:
            raise ValueError()
        
        if self.__has_active_keysymbol:
            self.__complete_keysymbol()
        
        if self.__has_active_sopheme:
            yield self.__complete_sopheme()



def parse_sopheme_sequence(seq: str) -> Generator[Sopheme, None, None]:
    parser = _Parser()

    for token in lex_sopheme_sequence(seq):
        yield from parser.consume(token)

    yield from parser.consume_eol()