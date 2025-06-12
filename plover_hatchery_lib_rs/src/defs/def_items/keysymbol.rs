use std::{
    collections::{HashSet}, sync::OnceLock
};

use pyo3::{prelude::*};
use regex::Regex;

use crate::defs::def_items::keysymbol;



#[pyclass]
#[derive(Clone, Debug)]
pub struct Keysymbol {
    symbol: String,
    base_symbol: String,
    stress: u8,
    optional: bool,
}

pub fn stress_marker(stress: u8) -> String {
    if stress <= 0 {
        return "".to_string();
    }

    format!("!{stress}")
}


impl Keysymbol {
    pub fn to_string(&self) -> String {
        let mut out = String::from(&self.symbol);

        out += &stress_marker(self.stress);

        if self.optional {
            out += "?";
        }

        out
    }
}

#[pymethods]
impl Keysymbol {
    #[new]
    pub fn new(symbol: String, stress: u8, optional: bool) -> Self {
        static KEYSYMBOL_SUB: OnceLock<Regex> = OnceLock::new();
        let keysymbol_sub = KEYSYMBOL_SUB.get_or_init(|| Regex::new(r"[\[\]\d]").unwrap());

        Keysymbol {
            base_symbol: keysymbol_sub.replace_all(symbol.as_str(), "").to_string(),
            symbol,
            stress,
            optional,
        }
    }

    #[staticmethod]
    pub fn new_with_known_base_symbol(symbol: String, base_symbol: String, stress: u8, optional: bool) -> Self {
        Keysymbol {
            symbol,
            base_symbol,
            stress,
            optional,
        }
    }

    
    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }

    #[getter]
    pub fn is_vowel(&self) -> bool {
        static VOWELS: OnceLock<HashSet<&str>> = OnceLock::new();
        let vowels = VOWELS.get_or_init(|| HashSet::<&str>::from_iter(
            [
                "e",
                "ao",
                "a",
                "ah",
                "oa",
                "aa",
                "ar",
                "eh",
                "ou",
                "ouw",
                "oou",
                "o",
                "au",
                "oo",
                "or",
                "our",
                "ii",
                "iy",
                "i",
                "@r",
                "@",
                "uh",
                "u",
                "uu",
                "iu",
                "ei",
                "ee",
                "ai",
                "ae",
                "aer",
                "aai",
                "oi",
                "oir",
                "ow",
                "owr",
                "oow",
                "ir",
                "@@r",
                "er",
                "eir",
                "ur",
                "i@",
            ]
                .into_iter()
        ));

        vowels.contains(self.base_symbol.as_str())
    }

    #[getter]
    pub fn is_consonant(&self) -> bool {
        !self.is_vowel()
    }
    
    #[getter]
    pub fn symbol(&self) -> &str {
        &self.symbol
    }

    #[getter]
    pub fn base_symbol(&self) -> &str {
        &self.base_symbol
    }

    #[getter]
    pub fn stress(&self) -> u8 {
        self.stress
    }

    #[getter]
    pub fn optional(&self) -> bool {
        self.optional
    }
}

#[pyclass]
#[derive(Clone, Debug)]
pub enum KeysymbolOptions {
    Leaf(Keysymbol),
    Leaves(Vec<Keysymbol>),
    Options(Vec<KeysymbolOptions>),
}

impl KeysymbolOptions {
    pub fn to_string(&self) -> String {
        let out = match self {
            KeysymbolOptions::Leaf(keysymbol) => keysymbol.to_string(),

            KeysymbolOptions::Leaves(keysymbols) => keysymbols.iter()
                .map(|keysymbol| keysymbol.to_string())
                .collect::<Vec<_>>()
                .join(" "),

            KeysymbolOptions::Options(options) => options.iter()
                .map(|option| option.to_string())
                .collect::<Vec<_>>()
                .join(" | "),
        };

        if self.needs_grouping() {
            format!("({out})")
        } else {
            out
        }
    }

    pub fn needs_grouping(&self) -> bool {
        match self {
            KeysymbolOptions::Leaf(_) => false,

            KeysymbolOptions::Leaves(keysymbols) => keysymbols.len() > 1,

            KeysymbolOptions::Options(options) => options.len() > 1,
        }
    }
}

