
use super::{
    rawable::{
        RawableEntity,
    },
    entity::{
        EntitySeq,
    },
};

use pyo3::prelude::*;


#[pyclass(get_all)]
#[derive(Clone, Debug)]
pub struct Def {
    pub rawables: Vec<RawableEntity>,
    pub varname: String,
}

impl Def {
    pub fn of(entity_seq: EntitySeq, varname: String) -> Def {
        Def {
            rawables: entity_seq.entities.into_iter()
                .map(|entity| RawableEntity::Entity(entity))
                .collect::<Vec<_>>(),
            varname,
        }
    }

    pub fn get_child(&self, index: usize) -> Option<&RawableEntity> {
        self.rawables.get(index)
    }

    pub fn new(rawables: Vec<RawableEntity>, varname: String) -> Def {
        Def {
            rawables,
            varname,
        }
    }
}