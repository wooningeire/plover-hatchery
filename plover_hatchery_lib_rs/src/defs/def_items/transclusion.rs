use pyo3::{prelude::*};


#[pyclass]
#[derive(Clone, Debug)]
pub struct Transclusion {
    #[pyo3(get)] pub target_varname: String,
    #[pyo3(get)] pub stress: u8
}

impl Transclusion {
    pub fn to_string(&self) -> String {
        let mut out = format!("{{{}}}", self.target_varname);

        if self.stress > 0 {
            out = format!("{}!{}", out, self.stress);
        }

        out
    }
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

    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }
}