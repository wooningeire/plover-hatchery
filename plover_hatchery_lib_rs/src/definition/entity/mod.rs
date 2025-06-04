use pyo3::{prelude::*};

mod sopheme;
pub use sopheme::{Sopheme, Keysymbol};

mod transclusion;
pub use transclusion::Transclusion;

use super::{DefDict, DefViewItem, RawableEntity};


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

impl Entity {
    pub fn get<'a>(&'a self, index: usize, defs: &'a DefDict) -> Result<Option<DefViewItem<'a>>, &'static str> {
        match self {
            Entity::Sopheme(sopheme) => Ok(sopheme.get(index).map(DefViewItem::Keysymbol)),

            Entity::Transclusion(transclusion) => defs.get(&transclusion.target_varname)
                .and_then(|seq| seq.entities.get(index))
                .map(|entity| Some(DefViewItem::Entity(entity)))
                .ok_or("entry not found"),
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