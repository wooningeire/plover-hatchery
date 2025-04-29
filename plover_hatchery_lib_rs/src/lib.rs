use pyo3::{prelude::*, wrap_pymodule};

#[pyclass]
struct Sophone {
    name: String,
}

#[pymethods]
impl Sophone {
    #[new]
    fn new(name: String) -> Sophone {
        Sophone {
            name,
        }
    }

    fn __str__(&self) -> &str {
        &self.name
    }
}


#[pyclass]
struct SophoneTypeRs {

}

#[pymethods]
impl SophoneTypeRs {
    #[staticmethod]
    fn mapper_from_sophones(sophone_names: &str) -> impl Fn() {
        || {

        }
    }
}



#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Sophone>()?;

    Ok(())
}
