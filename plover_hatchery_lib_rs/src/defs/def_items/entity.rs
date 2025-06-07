use pyo3::{prelude::*};


use super::{
    sopheme::Sopheme,
    transclusion::Transclusion,
};


#[pyclass]
#[derive(Clone, Debug)]
pub enum Entity {
    Sopheme(Sopheme),
    Transclusion(Transclusion),
}

#[pymethods]
impl Entity {
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

impl Entity {
    pub fn get_if_sopheme<'a>(&'a self) -> Option<&'a Sopheme> {
        match self {
            Entity::Sopheme(sopheme) => {
                Some(sopheme)
            },

            _ => None,
        }
    }
}


#[pyclass]
#[derive(Clone, Debug)]
pub struct EntitySeq {
    #[pyo3(get)] pub entities: Vec<Entity>,
}

#[pymethods]
impl EntitySeq {
    #[new]
    pub fn new(entities: Vec<Entity>) -> Self {
        EntitySeq {
            entities,
        }
    }
}