from dataclasses import dataclass
import dataclasses
from typing import TYPE_CHECKING, Callable, Generic, NamedTuple, TypeVar
from plover_hatchery.lib.sopheme.Sopheme import Sopheme

from ..Sopheme import Sopheme
from ..Keysymbol import Keysymbol
from .lex_sopheme_sequence import Token, TokenType, lex_sopheme_sequence

from plover_hatchery_lib_rs import Entity, Transclusion


@dataclass(frozen=True)
class _TokenCursor:
    tokens: tuple[Token, ...]
    current_token_index: int

    @property
    def token(self):
        return self.at(self.current_token_index)

    def at(self, index: int):
        if 0 <= index < len(self.tokens):
            return self.tokens[index]
        return Token(TokenType.WHITESPACE, "")

    def moved_to(self, index: int):
        return dataclasses.replace(self, current_token_index=index)
    
    def moved_by(self, increment: int):
        return dataclasses.replace(self, current_token_index=self.current_token_index + increment)

    def next(self):
        return self.moved_by(1)

    @property
    def token_is_dot(self):
        return self.token.type == TokenType.SYMBOL and self.token.value == "."

    @property
    def done(self):
        return self.current_token_index >= len(self.tokens)

    def __repr__(self):
        out_str = "\n"
        out_str += "".join(token.value for token in self.tokens) + "\n"
        out_str += "".join("." + ("~" * (len(token.value) - 1)) for token in self.tokens[:self.current_token_index]) + ("^") + "\n"
        out_str += repr(self.token) + "\n"
        return out_str


class ParserException(Exception):
    pass


T = TypeVar("T")
U = TypeVar("U")
if TYPE_CHECKING:
    class _ParseResult(NamedTuple, Generic[T]):
        value: T
        end_cursor: _TokenCursor

        def map(self, fn: Callable[[T], U]) -> "_ParseResult[U]": ...
else:
    class _ParseResult(NamedTuple):
        value: T
        end_cursor: _TokenCursor

        def map(self, fn: Callable[[T], U]) -> "_ParseResult[U]":
            return _ParseResult(fn(self.value), self.end_cursor)


def consume_stress(cursor: _TokenCursor):
    if cursor.token.type is not TokenType.SYMBOL or cursor.token.value != "!":
        return _ParseResult(0, cursor)

    stress = 1
    cursor = cursor.next()

    if cursor.token.type is TokenType.CHARS and cursor.token.value.isnumeric():
        stress = int(cursor.token.value)
        cursor = cursor.next()
    
    return _ParseResult(stress, cursor)
    

def consume_keysymbol(cursor: _TokenCursor):
    if cursor.token.type is not TokenType.CHARS:
        raise ParserException("Expected a keysymbol identifier here", cursor)

    chars = cursor.token.value
    cursor = cursor.next()

    stress, cursor = consume_stress(cursor)
    
    if cursor.token.type is not TokenType.SYMBOL or cursor.token.value != "?":
        return _ParseResult(Keysymbol(chars, stress, False), cursor)

    
    cursor = cursor.next()

    return _ParseResult(Keysymbol(chars, stress, True), cursor)


def consume_sopheme_ortho(cursor: _TokenCursor):
    if cursor.token.type is TokenType.CHARS:
        return _ParseResult(cursor.token.value, cursor.moved_by(1))

    if cursor.token_is_dot:
        return _ParseResult("", cursor)

    raise ParserException("Expected a sopheme orthography here", cursor)


def consume_sopheme_dot(cursor: _TokenCursor):
    if cursor.token_is_dot:
        return _ParseResult(None, cursor.next())
    
    raise ParserException("Expected a dot here", cursor)


def consume_sopheme_phono(cursor: _TokenCursor):
    if cursor.token.type is TokenType.CHARS:
        keysymbol, new_cursor = consume_keysymbol(cursor)
        return _ParseResult((keysymbol,), new_cursor)

    if cursor.token.type is TokenType.SYMBOL and cursor.token.value == "(":
        cursor = cursor.next()

        keysymbols: list[Keysymbol] = []
        while cursor.token.type is not TokenType.SYMBOL or cursor.token.value != ")":
            keysymbol, cursor = consume_keysymbol(cursor)
            keysymbols.append(keysymbol)

            if cursor.token.type is TokenType.WHITESPACE:
                cursor = cursor.next()

        cursor = cursor.next()

        return _ParseResult(tuple(keysymbols), cursor)

    if cursor.token.type is TokenType.WHITESPACE:
        return _ParseResult((), cursor)
    
    raise ParserException("Expected a sopheme phonology here", cursor)

def consume_sopheme(cursor: _TokenCursor):
    ortho, cursor = consume_sopheme_ortho(cursor)
    _, cursor = consume_sopheme_dot(cursor)
    phono, cursor = consume_sopheme_phono(cursor)

    return _ParseResult(Sopheme(ortho, list(phono)), cursor)


def consume_transclusion(cursor: _TokenCursor):
    if cursor.token.type is not TokenType.SYMBOL or cursor.token.value != "{":
        raise ParserException("Expected a transclusion here", cursor)

    cursor = cursor.next()

    if cursor.token.type is not TokenType.CHARS:
        raise ParserException("Expected a variable name here", cursor)
    
    varname = cursor.token.value
    cursor = cursor.next()

    if cursor.token.type is not TokenType.SYMBOL or cursor.token.value != "}":
        raise ParserException("Expected a closing brace here", cursor)

    cursor = cursor.next()
    
    stress, cursor = consume_stress(cursor)

    return _ParseResult(Transclusion(varname, stress), cursor)


def consume_entity(cursor: _TokenCursor):
    try:
        return consume_transclusion(cursor).map(Entity.transclusion)
    except ParserException: pass

    try:
        return consume_sopheme(cursor).map(Entity.sopheme)
    except ParserException: pass

    raise ParserException("Expected an entity here", cursor)


def parse_line(tokens: tuple[Token, ...]):
    cursor = _TokenCursor(tokens, 0)

    if cursor.done:
        return

    while True:
        entity, cursor = consume_entity(cursor)
        yield entity

        if cursor.done:
            break

        if cursor.token.type is TokenType.WHITESPACE:
            cursor = cursor.next()
        else:
            raise ParserException("Expected whitespace here", cursor)


def parse_entry_definition(seq: str):
    return parse_line(lex_sopheme_sequence(seq))


def parse_sopheme_seq_line(tokens: tuple[Token, ...]):
    cursor = _TokenCursor(tokens, 0)

    if cursor.done:
        return

    while True:
        sopheme, cursor = consume_sopheme(cursor)
        yield sopheme

        if cursor.done:
            break

        if cursor.token.type is TokenType.WHITESPACE:
            cursor = cursor.next()
        else:
            raise ParserException("Expected whitespace here", cursor)


def parse_sopheme_seq(seq: str):
    return parse_sopheme_seq_line(lex_sopheme_sequence(seq))