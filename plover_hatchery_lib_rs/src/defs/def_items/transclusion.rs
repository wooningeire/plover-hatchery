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


#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn to_string_reports_varname() {
        let transclusion = Transclusion::new("dragon".to_string(), 0);
        assert_eq!(transclusion.to_string(), "{dragon}");
    }

    #[test]
    fn to_string_reports_varname_and_stress() {
        let transclusion = Transclusion::new("amphi".to_string(), 1);
        assert_eq!(transclusion.to_string(), "{amphi}!1");
    }
}