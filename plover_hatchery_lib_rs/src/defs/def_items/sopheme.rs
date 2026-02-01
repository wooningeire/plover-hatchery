use pyo3::prelude::*;

use super::keysymbol::Keysymbol;


#[pyclass]
#[derive(Clone, Debug)]
pub struct Sopheme {
    #[pyo3(get)] pub chars: String,
    #[pyo3(get)] pub keysymbols: Vec<Keysymbol>,
}


#[pymethods]
impl Sopheme {
    #[new]
    pub fn new(chars: String, keysymbols: Vec<Keysymbol>) -> Self {
        Sopheme {
            chars,
            keysymbols,
        }
    }

    #[getter]
    pub fn can_be_silent(&self) -> bool {
        self.keysymbols.iter()
            .all(|keysymbol| keysymbol.optional())
    }

    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }
}


impl Sopheme {
    pub fn get_child<'a>(&'a self, index: usize) -> Option<&'a Keysymbol> {
        self.keysymbols.get(index)
    }

    pub fn to_string(&self) -> String {
        let mut keysymbols_string = self.keysymbols.iter()
            .map(|keysymbol| keysymbol.to_string())
            .collect::<Vec<_>>()
            .join(" ");

        if self.keysymbols.len() > 1 {
            keysymbols_string = format!("({keysymbols_string})");
        }

        format!("{chars}.{keysymbols_string}", chars=self.chars)
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
    use super::super::keysymbol::Keysymbol;

    #[test]
    fn to_string_reports_chars_and_keysymbols() {
        let sopheme = Sopheme::new("ph".to_string(), vec![
            Keysymbol::new("f".to_string(), 0, false),
        ]);
        assert_eq!(sopheme.to_string(), "ph.f");
    }

    #[test]
    fn to_string_reports_multikeysymbol_sophemes_in_parentheses() {
        let sopheme = Sopheme::new("u".to_string(), vec![
            Keysymbol::new("y".to_string(), 0, false), 
            Keysymbol::new("uu".to_string(), 1, false), 
        ]);
        assert_eq!(sopheme.to_string(), "u.(y uu!1)");
    }
}
