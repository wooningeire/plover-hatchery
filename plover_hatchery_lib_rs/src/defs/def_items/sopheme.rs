use pyo3::prelude::*;

use super::keysymbol::SoundSymbol;


#[pyclass]
#[derive(Clone, Debug)]
pub struct Sopheme {
    #[pyo3(get)] pub chars: String,
    pub sound_symbols: Vec<SoundSymbol>,
}


#[pymethods]
impl Sopheme {
    #[new]
    pub fn new(chars: String, sound_symbols: Vec<SoundSymbol>) -> Self {
        Sopheme {
            chars,
            sound_symbols,
        }
    }

    #[getter]
    pub fn sound_symbols(&self) -> Vec<SoundSymbol> {
        self.sound_symbols.clone()
    }

    #[getter]
    pub fn keysymbols(&self) -> Vec<SoundSymbol> {
        self.sound_symbols.clone()
    }

    #[getter]
    pub fn can_be_silent(&self) -> bool {
        self.sound_symbols.iter()
            .all(|sound_symbol| sound_symbol.optional())
    }

    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }
}


impl Sopheme {
    pub fn get_child<'a>(&'a self, index: usize) -> Option<&'a SoundSymbol> {
        self.sound_symbols.get(index)
    }

    pub fn to_string(&self) -> String {
        let mut sound_symbols_string = self.sound_symbols.iter()
            .map(|sound_symbol| sound_symbol.to_string())
            .collect::<Vec<_>>()
            .join(" ");

        if self.sound_symbols.len() > 1 {
            sound_symbols_string = format!("({sound_symbols_string})");
        }

        format!("{chars}.{sound_symbols_string}", chars=self.chars)
    }
}

#[pyclass]
pub struct SophemeSeq {
    pub items: Vec<Sopheme>,
}

#[pymethods]
impl SophemeSeq {
    #[new]
    pub fn new(sophemes: Vec<Sopheme>) -> Self {
        SophemeSeq {
            items: sophemes,
        }
    }
}


#[cfg(test)]
mod test {
    use super::*;
    use super::super::keysymbol::SoundSymbol;

    #[test]
    fn to_string_reports_chars_and_sound_symbols() {
        let sopheme = Sopheme::new("ph".to_string(), vec![
            SoundSymbol::new("f".to_string(), 0, false),
        ]);
        assert_eq!(sopheme.to_string(), "ph.f");
    }

    #[test]
    fn to_string_reports_multi_sound_symbol_sophemes_in_parentheses() {
        let sopheme = Sopheme::new("u".to_string(), vec![
            SoundSymbol::new("y".to_string(), 0, false), 
            SoundSymbol::new("uu".to_string(), 1, false), 
        ]);
        assert_eq!(sopheme.to_string(), "u.(y uu!1)");
    }
}
