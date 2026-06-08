use std::fmt::{self, Display, Formatter};
use super::lex::{Token, TokenClass, lex_sopheme_sequence};
use crate::defs::{Entity, Sopheme, Keysymbol, SoundSymbol, SoundSymbolKind, Transclusion};

#[derive(Debug, Clone)]
pub struct ParseErr {
    pub message: String,
    pub cursor_info: String,
}

impl Display for ParseErr {
    fn fmt(&self, formatter: &mut Formatter) -> fmt::Result {
        write!(formatter, "\n\n{}\n\n{}\n\n", self.message, self.cursor_info)
    }
}

impl std::error::Error for ParseErr {}

#[derive(Clone)]
struct TokenCursor<'a> {
    tokens: &'a [Token],
    current_token_index: usize,
}

impl<'a> TokenCursor<'a> {
    fn new(tokens: &'a [Token]) -> Self {
        TokenCursor {
            tokens,
            current_token_index: 0,
        }
    }

    fn token(&self) -> Token {
        self.at(self.current_token_index)
    }

    fn at(&self, index: usize) -> Token {
        self.tokens.get(index).cloned().unwrap_or_else(|| Token { 
            class: TokenClass::Whitespace, 
            value: String::new() 
        })
    }

    fn moved_to(&self, index: usize) -> Self {
        let mut new_cursor = self.clone();
        new_cursor.current_token_index = index;
        new_cursor
    }

    fn moved_by(&self, increment: isize) -> Self {
        let new_index = (self.current_token_index as isize + increment).max(0) as usize;
        self.moved_to(new_index)
    }

    fn next(&self) -> Self {
        self.moved_by(1)
    }

    fn token_is_dot(&self) -> bool {
        self.token_is_symbol(".")
    }

    fn token_is_symbol(&self, symbol: &str) -> bool {
        let token = self.token();
        token.class == TokenClass::Symbol && token.value == symbol
    }

    fn done(&self) -> bool {
        self.current_token_index >= self.tokens.len()
    }

    fn debug_string(&self) -> String {
        let mut out_str = String::from("\n");
        
        // Reconstruct the original string
        for token in self.tokens {
            out_str.push_str(&token.value);
        }
        out_str.push('\n');
        
        // Add position indicator
        for (i, token) in self.tokens.iter().enumerate() {
            if i < self.current_token_index {
                out_str.push('.');
                for _ in 1..token.value.len() {
                    out_str.push('~');
                }
            } else if i == self.current_token_index {
                out_str.push('^');
                break;
            }
        }
        out_str.push('\n');
        
        // Add current token info
        out_str.push_str(&format!("{:?}\n", self.token()));
        
        out_str
    }
}

struct ParseOk<'a, T> {
    value: T,
    end_cursor: TokenCursor<'a>,
}

impl<'a, T> ParseOk<'a, T> {
    fn new(value: T, end_cursor: TokenCursor<'a>) -> Self {
        ParseOk {
            value,
            end_cursor,
        }
    }

    fn map<U>(self, func: impl FnOnce(T) -> U) -> ParseOk<'a, U> {
        ParseOk::new(func(self.value), self.end_cursor.clone())
    }
}

fn consume_stress(cursor: TokenCursor) -> Result<ParseOk<u8>, ParseErr> {
    if cursor.token().class != TokenClass::Symbol || cursor.token().value != "!" {
        return Ok(ParseOk::new(0, cursor));
    }

    let mut stress = 1u8;
    let mut cursor = cursor.next();

    if cursor.token().class == TokenClass::Chars {
        match cursor.token().value.parse::<u8>() {
            Ok(value) => {
                stress = value;
                cursor = cursor.next();
            },

            Err(_) => return Err(ParseErr {
                message: "Expected a number here".to_string(),
                cursor_info: cursor.debug_string(),
            }),
        }
    }

    Ok(ParseOk::new(stress, cursor))
}

fn consume_delimited_sound_symbol_kind<'a>(
    cursor: TokenCursor<'a>,
    end_symbol: &str,
    kind_from_value: impl FnOnce(String) -> SoundSymbolKind,
) -> Result<ParseOk<'a, SoundSymbolKind>, ParseErr> {
    let mut cursor = cursor.next();
    let mut value = String::new();

    while !cursor.done() && !cursor.token_is_symbol(end_symbol) {
        if cursor.token().class == TokenClass::Whitespace {
            return Err(ParseErr {
                message: format!("Expected a closing {end_symbol} before whitespace"),
                cursor_info: cursor.debug_string(),
            });
        }

        value.push_str(&cursor.token().value);
        cursor = cursor.next();
    }

    if value.is_empty() {
        return Err(ParseErr {
            message: "Expected a sound symbol value here".to_string(),
            cursor_info: cursor.debug_string(),
        });
    }

    if !cursor.token_is_symbol(end_symbol) {
        return Err(ParseErr {
            message: format!("Expected a closing {end_symbol} here"),
            cursor_info: cursor.debug_string(),
        });
    }

    let cursor = cursor.next();

    Ok(ParseOk::new(kind_from_value(value), cursor))
}

fn consume_sound_symbol_kind(cursor: TokenCursor) -> Result<ParseOk<SoundSymbolKind>, ParseErr> {
    if cursor.token().class == TokenClass::Chars {
        return Ok(ParseOk::new(
            SoundSymbolKind::Abstract(cursor.token().value.clone()),
            cursor.next(),
        ));
    }

    if cursor.token_is_symbol("/") {
        return consume_delimited_sound_symbol_kind(
            cursor,
            "/",
            SoundSymbolKind::BroadIpa,
        );
    }

    if cursor.token_is_symbol("[") {
        return consume_delimited_sound_symbol_kind(
            cursor,
            "]",
            SoundSymbolKind::NarrowIpa,
        );
    }

    Err(ParseErr {
        message: "Expected a sound symbol identifier here".to_string(),
        cursor_info: cursor.debug_string(),
    })
}

fn consume_sound_symbol(cursor: TokenCursor) -> Result<ParseOk<SoundSymbol>, ParseErr> {
    let ParseOk { value: kind, end_cursor: cursor } = consume_sound_symbol_kind(cursor)?;
    let ParseOk { value: stress, end_cursor: cursor } = consume_stress(cursor)?;

    if !cursor.token_is_symbol("?") {
        return Ok(ParseOk::new(
            SoundSymbol::of(kind, stress, false),
            cursor
        ));
    }

    let cursor = cursor.next();

    Ok(ParseOk::new(
        SoundSymbol::of(kind, stress, true),
        cursor
    ))
}

fn consume_keysymbol(cursor: TokenCursor) -> Result<ParseOk<Keysymbol>, ParseErr> {
    consume_sound_symbol(cursor)
}

fn consume_keysymbol_seq(mut cursor: TokenCursor) -> Result<ParseOk<Vec<Keysymbol>>, ParseErr> {
    let mut keysymbols = Vec::new();

    while cursor.token().class != TokenClass::Symbol || cursor.token().value != ")" {
        let ParseOk { value: keysymbol, end_cursor: new_cursor } = consume_keysymbol(cursor)?;
        keysymbols.push(keysymbol);
        cursor = new_cursor;

        if cursor.token().class == TokenClass::Whitespace {
            cursor = cursor.next();
        }
    }

    Ok(ParseOk::new(keysymbols, cursor))
}

fn consume_sopheme_ortho(cursor: TokenCursor) -> Result<ParseOk<String>, ParseErr> {
    if cursor.token().class == TokenClass::Chars {
        return Ok(ParseOk::new(cursor.token().value.clone(), cursor.moved_by(1)));
    }

    if cursor.token_is_dot() {
        return Ok(ParseOk::new(String::new(), cursor));
    }

    Err(ParseErr {
        message: "Expected a sopheme orthography here".to_string(),
        cursor_info: cursor.debug_string(),
    })
}

fn consume_sopheme_dot(cursor: TokenCursor) -> Result<ParseOk<()>, ParseErr> {
    if cursor.token_is_dot() {
        return Ok(ParseOk::new((), cursor.next()));
    }

    Err(ParseErr {
        message: "Expected a dot here".to_string(),
        cursor_info: cursor.debug_string(),
    })
}

fn consume_sopheme_phono(mut cursor: TokenCursor) -> Result<ParseOk<Vec<Keysymbol>>, ParseErr> {
    if cursor.token().class == TokenClass::Chars
        || cursor.token_is_symbol("/")
        || cursor.token_is_symbol("[")
    {
        let ParseOk { value: keysymbol, end_cursor: new_cursor } = consume_keysymbol(cursor)?;
        return Ok(ParseOk::new(vec![keysymbol], new_cursor));
    }

    if cursor.token().class == TokenClass::Symbol && cursor.token().value == "(" {
        cursor = cursor.next();

        let ParseOk {
            value: keysymbols,
            end_cursor: mut cursor,
        } = consume_keysymbol_seq(cursor)?;

        cursor = cursor.next();

        return Ok(ParseOk::new(keysymbols, cursor));
    }

    if cursor.token().class == TokenClass::Whitespace {
        return Ok(ParseOk::new(vec![], cursor));
    }

    Err(ParseErr {
        message: "Expected a sopheme phonology here".to_string(),
        cursor_info: cursor.debug_string(),
    })
}

fn consume_sopheme(cursor: TokenCursor) -> Result<ParseOk<Sopheme>, ParseErr> {
    let ParseOk { value: ortho, end_cursor: cursor } = consume_sopheme_ortho(cursor)?;
    let ParseOk { value: _, end_cursor: cursor } = consume_sopheme_dot(cursor)?;
    let ParseOk { value: phono, end_cursor: cursor } = consume_sopheme_phono(cursor)?;

    Ok(ParseOk::new(Sopheme::new(ortho, phono), cursor))
}

fn consume_transclusion(cursor: TokenCursor) -> Result<ParseOk<Transclusion>, ParseErr> {
    if cursor.token().class != TokenClass::Symbol || cursor.token().value != "{" {
        return Err(ParseErr {
            message: "Expected a transclusion here".to_string(),
            cursor_info: cursor.debug_string(),
        });
    }

    let cursor = cursor.next();

    if cursor.token().class != TokenClass::Chars {
        return Err(ParseErr {
            message: "Expected a variable name here".to_string(),
            cursor_info: cursor.debug_string(),
        });
    }

    let varname = cursor.token().value.clone();
    let cursor = cursor.next();

    if cursor.token().class != TokenClass::Symbol || cursor.token().value != "}" {
        return Err(ParseErr {
            message: "Expected a closing brace here".to_string(),
            cursor_info: cursor.debug_string(),
        });
    }

    let cursor = cursor.next();

    let ParseOk { value: stress, end_cursor: cursor } = consume_stress(cursor)?;

    Ok(ParseOk::new(Transclusion::new(varname, stress), cursor))
}

fn consume_entity(cursor: TokenCursor) -> Result<ParseOk<Entity>, ParseErr> {
    // Try transclusion first
    if let Ok(result) = consume_transclusion(cursor.clone()) {
        return Ok(result.map(Entity::Transclusion));
    }

    // Try sopheme
    if let Ok(result) = consume_sopheme(cursor.clone()) {
        return Ok(result.map(Entity::Sopheme));
    }

    Err(ParseErr {
        message: "Expected an entity here".to_string(),
        cursor_info: cursor.debug_string(),
    })
}

fn parse_line(tokens: &[Token]) -> Result<Vec<Entity>, ParseErr> {
    let mut cursor = TokenCursor::new(tokens);
    let mut entities = Vec::new();

    if cursor.done() {
        return Ok(entities);
    }

    loop {
        let ParseOk { value: entity, end_cursor: new_cursor } = consume_entity(cursor)?;
        entities.push(entity);
        cursor = new_cursor;

        if cursor.done() {
            break;
        }

        if cursor.token().class == TokenClass::Whitespace {
            cursor = cursor.next();
        } else {
            return Err(ParseErr {
                message: "Expected whitespace here".to_string(),
                cursor_info: cursor.debug_string(),
            });
        }
    }

    Ok(entities)
}

pub fn parse_entry_definition(seq: &str) -> Result<Vec<Entity>, ParseErr> {
    parse_line(&lex_sopheme_sequence(seq))
}

fn parse_sopheme_seq_line(tokens: &[Token]) -> Result<Vec<Sopheme>, ParseErr> {
    let mut cursor = TokenCursor::new(tokens);
    let mut sophemes = Vec::new();

    if cursor.done() {
        return Ok(sophemes);
    }

    loop {
        let ParseOk { value: sopheme, end_cursor: new_cursor } = consume_sopheme(cursor)?;
        sophemes.push(sopheme);
        cursor = new_cursor;

        if cursor.done() {
            break;
        }

        if cursor.token().class == TokenClass::Whitespace {
            cursor = cursor.next();
        } else {
            return Err(ParseErr {
                message: "Expected whitespace here".to_string(),
                cursor_info: cursor.debug_string(),
            });
        }
    }

    Ok(sophemes)
}

pub fn parse_sopheme_seq(seq: &str) -> Result<Vec<Sopheme>, ParseErr> {
    parse_sopheme_seq_line(&lex_sopheme_sequence(seq))
}

pub fn parse_sound_symbol_seq(seq: &str) -> Result<Vec<SoundSymbol>, ParseErr> {
    let tokens = lex_sopheme_sequence(seq);
    let mut cursor = TokenCursor::new(&tokens);
    let mut sound_symbols = Vec::new();

    if cursor.done() {
        return Ok(sound_symbols);
    }

    loop {
        let ParseOk { value: sound_symbol, end_cursor: new_cursor } = consume_sound_symbol(cursor)?;
        sound_symbols.push(sound_symbol);
        cursor = new_cursor;

        if cursor.done() {
            break;
        }

        if cursor.token().class == TokenClass::Whitespace {
            cursor = cursor.next();
        } else {
            return Err(ParseErr {
                message: "Expected whitespace here".to_string(),
                cursor_info: cursor.debug_string(),
            });
        }
    }

    Ok(sound_symbols)
}

pub fn parse_keysymbol_seq(seq: &str) -> Result<Vec<Keysymbol>, ParseErr> {
    parse_sound_symbol_seq(seq)
}

#[cfg(test)]
mod test {
    use super::*;

    
    fn is_parsing_reversible(sopheme_seq: &str) -> Result<(), ParseErr> {
        assert_eq!(
            sopheme_seq,
            parse_entry_definition(sopheme_seq)?
                .iter()
                .map(|entity| entity.to_string())
                .collect::<Vec<_>>()
                .join(" ")
        );

        Ok(())
    }


    #[test]
    fn single_sopheme() {
        is_parsing_reversible("a.@!2?").unwrap();
    }

    #[test]
    fn multiple_sophemes() {
        is_parsing_reversible("h.h y.ae!1 d.d r.r o.@ g.jh e.E5 n.n").unwrap();
    }

    #[test]
    fn keysymbol_groups() {
        is_parsing_reversible("a.a n.ng x.(g z) i.ae!1 e.@ t.t y.iy").unwrap();
    }

    #[test]
    fn bare_sound_symbols_are_abstract() {
        let sound_symbols = parse_sound_symbol_seq("ae ng").unwrap();

        assert_eq!(
            sound_symbols.iter()
                .map(|sound_symbol| sound_symbol.kind())
                .collect::<Vec<_>>(),
            vec![
                SoundSymbolKind::Abstract("ae".to_string()),
                SoundSymbolKind::Abstract("ng".to_string()),
            ],
        );
    }

    #[test]
    fn broad_and_narrow_ipa_sound_symbols_are_reversible() {
        is_parsing_reversible("h.[h] a.ae ng./ŋ/").unwrap();
    }

    #[test]
    fn keysymbol_options_are_rejected() {
        assert!(parse_entry_definition("z.z e.ii|ee!1 t.t a.@").is_err());
    }

    #[test]
    fn keysymbol_group_options_are_rejected() {
        assert!(parse_entry_definition("'. oeu.(@@r!1 r)|uh v.v r.r e.@1 s.").is_err());
    }
} 
