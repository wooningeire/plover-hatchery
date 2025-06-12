
use super::{
    entity::{
        Entity,
    },
};

use pyo3::prelude::*;


#[pyclass(get_all)]
#[derive(Clone, Debug)]
pub struct Def {
    pub entities: Vec<Entity>,
    pub varname: String,
}

impl Def {
    pub fn of(entities: Vec<Entity>, varname: String) -> Def {
        Def {
            entities,
            varname,
        }
    }

    pub fn get_child(&self, index: usize) -> Option<&Entity> {
        self.entities.get(index)
    }

    pub fn new(entities: Vec<Entity>, varname: String) -> Def {
        Def {
            entities,
            varname,
        }
    }

    pub fn to_string(&self) -> String {
        format!(
            "{} = {}",
            self.varname,
            self.entities.iter()
                .map(|entities| entities.to_string())
                .collect::<Vec<_>>()
                .join(" ")
        )
    }
}

#[pymethods]
impl Def {
    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }
}