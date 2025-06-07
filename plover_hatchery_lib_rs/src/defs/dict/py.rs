use super::{
    EntitySeq,
    Def,
};

use pyo3::prelude::*;


#[pyclass]
pub struct DefDict {
    pub dict: Box<super::DefDict>,
}

#[pymethods]
impl DefDict {
    #[new]
    pub fn new() -> Self {
        DefDict {
            dict: Box::new(super::DefDict::new()),
        }
    }

    pub fn add(&mut self, varname: String, seq: EntitySeq) {
        self.dict.add(varname, seq);
    }

    pub fn get_def(&self, varname: &str) -> Option<Def> {
        self.dict.get_def(varname)
    }

    pub fn foreach_key(&self, py: Python<'_>, callable: PyObject) {
        for varname in self.dict.entries.keys() {
            _ = callable.call(py, (varname.to_string(),), None);
        }
    }
}