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

    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
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

    pub fn to_string(&self) -> String {
        match self {
            Entity::Sopheme(sopheme) => sopheme.to_string(),

            Entity::Transclusion(transclusion) => transclusion.to_string(),
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