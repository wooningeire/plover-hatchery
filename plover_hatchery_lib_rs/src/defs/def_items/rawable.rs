use super::{
    entity::Entity,
    Def,
};

use pyo3::prelude::*;


#[pyclass]
#[derive(Clone, Debug)]
pub enum RawableEntity {
    Entity(Entity),
    RawDef(Def),
}

impl RawableEntity {
    pub fn to_string(&self) -> String {
        match self {
            RawableEntity::Entity(entity) => entity.to_string(),

            RawableEntity::RawDef(def) => format!("({})", def.to_string()),
        }
    }
}

#[pymethods]
impl RawableEntity {
    pub fn maybe_entity(&self) -> Option<Entity> {
        match self {
            RawableEntity::Entity(entity) => Some(entity.clone()),

            _ => None,
        }
    }

    pub fn maybe_raw_def(&self) -> Option<Def> {
        match self {
            RawableEntity::RawDef(def) => Some(def.clone()),

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
