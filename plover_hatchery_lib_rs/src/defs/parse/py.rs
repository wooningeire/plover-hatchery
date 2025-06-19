use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use super::{
    parse::{parse_entry_definition, parse_sopheme_seq, parse_keysymbol_seq},
};

#[pyfunction]
#[pyo3(name = "parse_entry_definition")]
pub fn py_parse_entry_definition(seq: &str) -> PyResult<Vec<crate::defs::Entity>> {
    parse_entry_definition(seq)
        .map_err(|e| PyValueError::new_err(format!("{}", e)))
}

#[pyfunction]
#[pyo3(name = "parse_sopheme_seq")]
pub fn py_parse_sopheme_seq(seq: &str) -> PyResult<Vec<crate::defs::Sopheme>> {
    parse_sopheme_seq(seq)
        .map_err(|e| PyValueError::new_err(format!("{}", e)))
}

#[pyfunction]
#[pyo3(name = "parse_keysymbol_seq")]
pub fn py_parse_keysymbol_seq(seq: &str) -> PyResult<Vec<crate::defs::Keysymbol>> {
    parse_keysymbol_seq(seq)
        .map_err(|e| PyValueError::new_err(format!("{}", e)))
}