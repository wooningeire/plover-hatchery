use pyo3::{prelude::*};


use super::{
    sopheme::Sopheme,
    transclusion::Transclusion,
};

use super::{DefDict, DefViewItemRef};


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
    pub fn get<'a>(&'a self, index: usize, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        match self {
            Entity::Sopheme(sopheme) => sopheme.get(index).map(DefViewItemRef::Keysymbol).map(Ok),

            Entity::Transclusion(transclusion) => Some(
                defs.get(&transclusion.target_varname)
                    .and_then(|seq| seq.entities.get(index))
                    .map(DefViewItemRef::Entity)
                    .ok_or("entry not found")
            ),
        }
    }

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
#[derive(Clone)]
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