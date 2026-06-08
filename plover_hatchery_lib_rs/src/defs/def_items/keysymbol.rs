use std::{
    collections::{HashSet},
    hash::{DefaultHasher, Hasher, Hash},
    sync::OnceLock,
};

use pyo3::{prelude::*};


#[pyclass]
#[derive(Clone, Debug, Hash, Eq, PartialEq)]
pub enum SoundSymbolKind {
    Abstract(String),
    BroadIpa(String),
    NarrowIpa(String),
}

impl SoundSymbolKind {
    pub fn value_ref(&self) -> &str {
        match self {
            SoundSymbolKind::Abstract(value) => value,
            SoundSymbolKind::BroadIpa(value) => value,
            SoundSymbolKind::NarrowIpa(value) => value,
        }
    }

    pub fn kind_name_ref(&self) -> &str {
        match self {
            SoundSymbolKind::Abstract(_) => "abstract",
            SoundSymbolKind::BroadIpa(_) => "broad-ipa",
            SoundSymbolKind::NarrowIpa(_) => "narrow-ipa",
        }
    }

    pub fn to_string(&self) -> String {
        match self {
            SoundSymbolKind::Abstract(value) => value.clone(),
            SoundSymbolKind::BroadIpa(value) => format!("/{value}/"),
            SoundSymbolKind::NarrowIpa(value) => format!("[{value}]"),
        }
    }
}

#[pymethods]
impl SoundSymbolKind {
    #[staticmethod]
    pub fn abstract_symbol(value: String) -> Self {
        SoundSymbolKind::Abstract(value)
    }

    #[staticmethod]
    pub fn broad_ipa(value: String) -> Self {
        SoundSymbolKind::BroadIpa(value)
    }

    #[staticmethod]
    pub fn narrow_ipa(value: String) -> Self {
        SoundSymbolKind::NarrowIpa(value)
    }

    #[getter]
    pub fn value(&self) -> &str {
        self.value_ref()
    }

    #[getter]
    pub fn kind_name(&self) -> &str {
        self.kind_name_ref()
    }

    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }
}

#[pyclass]
#[derive(Clone, Debug, Hash, Eq, PartialEq)]
pub struct SoundSymbol {
    kind: SoundSymbolKind,
    stress: u8,
    optional: bool,
}

pub fn stress_marker(stress: u8) -> String {
    if stress <= 0 {
        return "".to_string();
    }

    format!("!{stress}")
}


impl SoundSymbol {
    pub fn of(kind: SoundSymbolKind, stress: u8, optional: bool) -> Self {
        SoundSymbol {
            kind,
            stress,
            optional,
        }
    }

    pub fn abstract_symbol(value: String, stress: u8, optional: bool) -> Self {
        SoundSymbol::of(SoundSymbolKind::Abstract(value), stress, optional)
    }

    pub fn broad_ipa(value: String, stress: u8, optional: bool) -> Self {
        SoundSymbol::of(SoundSymbolKind::BroadIpa(value), stress, optional)
    }

    pub fn narrow_ipa(value: String, stress: u8, optional: bool) -> Self {
        SoundSymbol::of(SoundSymbolKind::NarrowIpa(value), stress, optional)
    }

    pub fn to_string(&self) -> String {
        let mut out = self.kind.to_string();

        out += &stress_marker(self.stress);

        if self.optional {
            out += "?";
        }

        out
    }
}

#[pymethods]
impl SoundSymbol {
    #[new]
    pub fn new(value: String, stress: u8, optional: bool) -> Self {
        SoundSymbol::abstract_symbol(value, stress, optional)
    }

    #[staticmethod]
    pub fn new_abstract(value: String, stress: u8, optional: bool) -> Self {
        SoundSymbol::abstract_symbol(value, stress, optional)
    }

    #[staticmethod]
    pub fn new_broad_ipa(value: String, stress: u8, optional: bool) -> Self {
        SoundSymbol::broad_ipa(value, stress, optional)
    }

    #[staticmethod]
    pub fn new_narrow_ipa(value: String, stress: u8, optional: bool) -> Self {
        SoundSymbol::narrow_ipa(value, stress, optional)
    }

    #[staticmethod]
    pub fn new_with_known_base_symbol(symbol: String, _base_symbol: String, stress: u8, optional: bool) -> Self {
        SoundSymbol::abstract_symbol(symbol, stress, optional)
    }

    
    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }

    pub fn __hash__(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.hash(&mut hasher);
        hasher.finish()
    }

    pub fn __eq__(&self, other: &SoundSymbol) -> bool {
        self == other
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
        static IPA_VOWELS: OnceLock<HashSet<&str>> = OnceLock::new();
        let ipa_vowels = IPA_VOWELS.get_or_init(|| HashSet::<&str>::from_iter(
            [
                "a",
                "æ",
                "ɑ",
                "ɒ",
                "ɔ",
                "e",
                "ə",
                "ɛ",
                "ɜ",
                "i",
                "ɪ",
                "o",
                "ʊ",
                "u",
                "ʌ",
            ]
                .into_iter()
        ));

        match &self.kind {
            SoundSymbolKind::Abstract(value) => vowels.contains(value.as_str()),
            SoundSymbolKind::BroadIpa(value) => ipa_vowels.contains(value.as_str()),
            SoundSymbolKind::NarrowIpa(value) => ipa_vowels.contains(value.as_str()),
        }
    }

    #[getter]
    pub fn is_consonant(&self) -> bool {
        !self.is_vowel()
    }
    
    #[getter]
    pub fn kind(&self) -> SoundSymbolKind {
        self.kind.clone()
    }

    #[getter]
    pub fn value(&self) -> &str {
        self.kind.value_ref()
    }

    #[getter]
    pub fn symbol(&self) -> &str {
        self.value()
    }

    #[getter]
    pub fn base_symbol(&self) -> &str {
        self.value()
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
pub enum SoundSymbolOptions {
    Leaf(SoundSymbol),
    Leaves(Vec<SoundSymbol>),
    Options(Vec<SoundSymbolOptions>),
}

impl SoundSymbolOptions {
    pub fn to_string(&self) -> String {
        let out = match self {
            SoundSymbolOptions::Leaf(sound_symbol) => sound_symbol.to_string(),

            SoundSymbolOptions::Leaves(sound_symbols) => sound_symbols.iter()
                .map(|sound_symbol| sound_symbol.to_string())
                .collect::<Vec<_>>()
                .join(" "),

            SoundSymbolOptions::Options(options) => options.iter()
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
            SoundSymbolOptions::Leaf(_) => false,

            SoundSymbolOptions::Leaves(sound_symbols) => sound_symbols.len() > 1,

            SoundSymbolOptions::Options(options) => options.len() > 1,
        }
    }
}

pub type Keysymbol = SoundSymbol;



#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn abstract_sound_symbols_render_like_legacy_keysymbols() {
        let sound_symbol = SoundSymbol::abstract_symbol("a".to_string(), 0, false);
        assert_eq!(sound_symbol.to_string(), "a");
    }

    #[test]
    fn to_string_reports_stress_number() {
        let sound_symbol = SoundSymbol::abstract_symbol("ee".to_string(), 1, false);
        assert_eq!(sound_symbol.to_string(), "ee!1");
    }

    #[test]
    fn to_string_reports_optional() {
        let sound_symbol = SoundSymbol::abstract_symbol("@@r".to_string(), 0, true);
        assert_eq!(sound_symbol.to_string(), "@@r?");
    }

    #[test]
    fn to_string_reports_all() {
        let sound_symbol = SoundSymbol::abstract_symbol("i".to_string(), 3, true);
        assert_eq!(sound_symbol.to_string(), "i!3?");
    }

    #[test]
    fn to_string_marks_broad_ipa() {
        let sound_symbol = SoundSymbol::broad_ipa("ŋ".to_string(), 0, false);
        assert_eq!(sound_symbol.to_string(), "/ŋ/");
    }

    #[test]
    fn to_string_marks_narrow_ipa() {
        let sound_symbol = SoundSymbol::narrow_ipa("h".to_string(), 0, false);
        assert_eq!(sound_symbol.to_string(), "[h]");
    }
}
