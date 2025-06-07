use super::{
    entity::Entity,
    Def,
    DefDict,
    DefViewItemRef,
};

use pyo3::prelude::*;


#[pyclass]
#[derive(Clone, Debug)]
pub enum RawableEntity {
    Entity(Entity),
    RawDef(Def),
}

impl RawableEntity {
    pub fn get<'a>(&'a self, index: usize, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        match self {
            RawableEntity::Entity(entity) => entity.get(index, defs),

            RawableEntity::RawDef(def) => def.get(index).map(Ok),
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
}
