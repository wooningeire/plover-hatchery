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
}
