use super::{
    sopheme::Sopheme,
    transclusion::Transclusion,
    def::Def,
};

use pyo3::prelude::*;


#[pyclass]
#[derive(Clone, Debug)]
pub enum Entity {
    Sopheme(Sopheme),
    Transclusion(Transclusion),
    RawDef(Def),
}

impl Entity {
    pub fn to_string(&self) -> String {
        match self {
            Entity::Sopheme(sopheme) => sopheme.to_string(),

            Entity::Transclusion(transclusion) => transclusion.to_string(),

            Entity::RawDef(def) => format!("({})", def.to_string()),
        }
    }
}

#[pymethods]
impl Entity {
    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }
}
