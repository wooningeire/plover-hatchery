use pyo3::prelude::*;

#[derive(Debug, Clone)]
#[pyclass]
pub struct TransitionFlag {
    #[pyo3(get, set)]
    pub label: String,
}

#[pymethods]
impl TransitionFlag {
    #[new]
    pub fn new(label: String) -> Self {
        Self {
            label,
        }
    }
}