use pyo3::{prelude::*};


#[pyclass]
#[derive(Clone)]
pub struct Transclusion {
    target_varname: String,
    stress: u8
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