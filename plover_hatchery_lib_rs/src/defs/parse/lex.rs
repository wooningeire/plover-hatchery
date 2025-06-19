#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TokenClass {
    Start,
    Whitespace,
    Chars,
    Symbol,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Token {
    pub class: TokenClass,
    pub value: String,
}

impl Token {
    pub fn new(token_type: TokenClass, value: String) -> Self {
        Token { class: token_type, value }
    }
}

struct Lexer {
    state: TokenClass,
    current_token: String,
}

impl Lexer {
    fn new() -> Self {
        Lexer {
            state: TokenClass::Start,
            current_token: String::new(),
        }
    }

    fn step(&mut self, ch: char, target_state: TokenClass) -> Option<Token> {
        if self.state != TokenClass::Symbol && self.state == target_state {
            self.state = target_state;
            self.current_token.push(ch);
            return None;
        }

        let token = if self.state != TokenClass::Start {
            Some(Token::new(self.state, self.current_token.clone()))
        } else {
            None
        };

        self.state = target_state;
        self.current_token = ch.to_string();

        token
    }

    fn step_eol(self) -> Token {
        Token::new(self.state, self.current_token)
    }
}

pub fn lex_sopheme_sequence(seq: &str) -> Vec<Token> {
    let mut lexer = Lexer::new();
    let mut tokens = Vec::new();

    for ch in seq.chars() {
        let token = if ch == ' ' {
            lexer.step(ch, TokenClass::Whitespace)
        } else if ch.is_alphanumeric() || "-@#^':".contains(ch) {
            lexer.step(ch, TokenClass::Chars)
        } else {
            lexer.step(ch, TokenClass::Symbol)
        };

        if let Some(t) = token {
            tokens.push(t);
        }
    }

    tokens.push(lexer.step_eol());
    tokens
} 