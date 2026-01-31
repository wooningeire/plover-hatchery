use super::super::{
    def_items::{
        Entity,
        Def,
    },
    dict::DefDict,
};

use pyo3::prelude::*;


#[pyclass]
#[pyo3(name = "DefDict")]
pub struct PyDefDict {
    pub dict: Box<DefDict>,
}

#[pymethods]
impl PyDefDict {
    #[new]
    pub fn new() -> Self {
        PyDefDict {
            dict: Box::new(DefDict::new()),
        }
    }

    pub fn add(&mut self, varname: String, entities: Vec<Entity>) {
        self.dict.add(varname, entities);
    }

    pub fn get_def(&self, varname: &str) -> Option<Def> {
        self.dict.get_def(varname)
    }

    pub fn foreach_key(&self, py: Python, callable: Py<PyAny>) {
        for varname in self.dict.entries.keys() {
            _ = callable.call(py, (varname.to_string(),), None);
        }
    }
}