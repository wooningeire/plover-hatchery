use pyo3::{prelude::*, wrap_pymodule};

#[pyclass]
struct Transclusion {
    target_varname: String,
    stress: u8
}

#[pymethods]
impl Transclusion {
    #[new]
    fn new(target_varname: String, stress: u8) -> Self {
        Transclusion {
            target_varname,
            stress,
        }
    }
}

#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Transclusion>()?;

    Ok(())
}
