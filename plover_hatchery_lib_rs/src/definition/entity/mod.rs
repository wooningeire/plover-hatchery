use pyo3::{prelude::*};

mod sopheme;
pub use sopheme::{Sopheme, Keysymbol};

pub mod transclusion;
pub use transclusion::Transclusion;


#[pyclass]
#[derive(Clone)]
pub enum Entity {
    Sopheme(Sopheme),
    Transclusion(Transclusion),
}

#[pymethods]
impl Entity {
    #[staticmethod]
    pub fn sopheme(sopheme: Sopheme) -> Self {
        Entity::Sopheme(sopheme)
    }

    #[staticmethod]
    pub fn transclusion(transclusion: Transclusion) -> Self {
        Entity::Transclusion(transclusion)
    }

    #[getter]
    pub fn maybe_sopheme(&self) -> Option<Sopheme> {
        match self {
            Entity::Sopheme(sopheme) => Some(sopheme.clone()),
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