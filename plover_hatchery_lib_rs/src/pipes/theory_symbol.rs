use std::hash::{DefaultHasher, Hasher, Hash};

use pyo3::prelude::*;
use pyo3::types::PyTuple;

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
#[pyclass]
pub struct TheorySymbol {
    #[pyo3(get)] value: String,
}

impl TheorySymbol {
    fn to_string(&self) -> String {
        self.value.clone()
    }
}

#[pymethods]
impl TheorySymbol {
    #[new]
    pub fn new(value: String) -> Self {
        Self {
            value,
        }
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

    pub fn __eq__(&self, other: &TheorySymbol) -> bool {
        self == other
    }

    #[staticmethod]
    fn parse_seq<'py>(seq: &str, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        let theory_symbols = seq.split_whitespace()
            .map(|segment| TheorySymbol::new(segment.to_string()))
            .collect::<Vec<TheorySymbol>>();

        PyTuple::new(py, theory_symbols)
    }
}