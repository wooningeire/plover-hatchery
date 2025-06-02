use std::sync::Arc;

use pyo3::{prelude::*, types::PyList};

mod keysymbol;
pub use keysymbol::Keysymbol;


#[pyclass]
#[derive(Clone)]
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
        let mut keysymbols_string = self.keysymbols.iter()
            .map(|keysymbol| keysymbol.to_string())
            .collect::<Vec<_>>()
            .join(" ");

        if self.keysymbols.len() > 1 {
            keysymbols_string = format!("({keysymbols_string})");
        }

        format!("{chars}.{keysymbols_string}", chars=self.chars)
    }

    pub fn __repr__(&self) -> String {
        self.__str__()
    }
}