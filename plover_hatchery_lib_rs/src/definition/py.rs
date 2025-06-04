
use std::sync::Arc;

use pyo3::{prelude::*, exceptions::PyException};

use super::*;



#[pyclass]
pub struct DefDict {
    dict: Box<super::DefDict>,
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


#[pyclass(get_all)]
pub struct DefView {
    defs: Py<DefDict>,
    root_def: Py<Def>,
}

impl DefView {
    fn with_rs<T>(&self, py: Python<'_>, func: impl Fn(super::DefView) -> T) -> T {
        let defs = self.defs.borrow(py);
        let root_def = self.root_def.borrow(py);
        let view_rs = super::DefView::new_ref(&defs.dict, &root_def);

        func(view_rs)
    }

    fn with_rs_result<T>(&self, py: Python<'_>, func: impl Fn(super::DefView) -> Result<T, &'static str>) -> Result<T, PyErr> {
        self.with_rs(py, func)
            .map_err(|msg| PyException::new_err(msg))
    }
}

#[pymethods]
impl DefView {
    #[new]
    pub fn new(defs: Py<DefDict>, root_def: Py<Def>) -> Self {
        DefView {
            defs,
            root_def,
        }
    }

    pub fn collect_sophemes(&self, py: Python<'_>) -> Result<SophemeSeq, PyErr> {
        self.with_rs_result(py, |view_rs| view_rs.collect_sophemes())
    }


    pub fn translation(&self, py: Python<'_>) -> Result<String, PyErr> {
        self.with_rs_result(py, |view_rs| view_rs.translation())
    }


    pub fn foreach_step(&self, py: Python<'_>, callable: PyObject) {
        self.with_rs(py, |view_rs| {
            let mut cursor = DefViewCursor::new(&view_rs);

            while let Some(dir) = cursor.step() {
                _ = callable.call(py, (dir,), None);
            }
        });
    }

    // pub fn foreach_sopheme(&self, py: Python<'_>, callable: PyObject) {
    //     self.with_rs(py, |view_rs| {
    //         view_rs.sophemes().for_each(|item| {
    //             _ = callable.call(py, (item.cursor.clone(),), None);
    //         });
    //     });
    // }

    // pub fn loc_first_keysymbol() {

    // }
}
