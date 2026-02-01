
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
    fn __str__(&self) -> String {
        self.to_string()
    }

    fn __repr__(&self) -> String {
        self.to_string()
    }
}


#[cfg(test)]
mod test {
    use super::*;
    use super::super::transclusion::Transclusion;

    #[test]
    fn to_string_reports_varname_and_entities() {
        let def = Def::of(vec![
            Entity::Transclusion(Transclusion::new("amphi".to_string(), 1)), 
            Entity::Transclusion(Transclusion::new("vern".to_string(), 2)), 
        ], "amphivern".to_string());

        assert_eq!(def.to_string(), "amphivern = {amphi}!1 {vern}!2");
    }
}