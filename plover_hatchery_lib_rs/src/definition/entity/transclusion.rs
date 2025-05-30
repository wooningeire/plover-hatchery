use pyo3::{prelude::*};


#[pyclass]
#[derive(Clone)]
pub struct Transclusion {
    #[pyo3(get)] pub target_varname: String,
    #[pyo3(get)] pub stress: u8
}

#[pymethods]
impl Transclusion {
    #[new]
    pub fn new(target_varname: String, stress: u8) -> Self {
        Transclusion {
            target_varname,
            stress,
        }
    }
}