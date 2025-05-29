use pyo3::{prelude::*};

pub mod sopheme;
pub mod transclusion;

use transclusion::Transclusion;

#[pyclass]
pub enum Entity {
    Sopheme(PyObject),
    Transclusion(Transclusion),
}

#[pymethods]
impl Entity {
    #[staticmethod]
    pub fn sopheme(sopheme: PyObject) -> Self {
        Entity::Sopheme(sopheme)
    }

    #[staticmethod]
    pub fn transclusion(transclusion: Transclusion) -> Self {
        Entity::Transclusion(transclusion)
    }

    #[getter]
    pub fn maybe_sopheme(&self) -> Option<&PyObject> {
        match self {
            Entity::Sopheme(sopheme) => Some(sopheme),
            _ => None,
        }
    }

    #[getter]
    pub fn maybe_transclusion(&self) -> Option<Transclusion> {
        match self {
            Entity::Transclusion(transclusion) => Some(transclusion.clone()),
            _ => None,
        }
    }
}