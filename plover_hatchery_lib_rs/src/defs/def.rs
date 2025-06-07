
use super::{
    def_items::{
        RawableEntity,
        EntitySeq,
    },
    view::DefViewItemRef,
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

    pub fn get<'a>(&'a self, index: usize) -> Option<DefViewItemRef<'a>> {
        self.rawables.get(index)
            .map(DefViewItemRef::Rawable)
    }

    pub fn new(rawables: Vec<RawableEntity>, varname: String) -> Def {
        Def {
            rawables,
            varname,
        }
    }

    pub fn empty(varname: String) -> Def {
        Def {
            rawables: vec![],
            varname,
        }
    }
}