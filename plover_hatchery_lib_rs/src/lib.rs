mod entity;

use entity::{
    Entity,
    transclusion::Transclusion,
};

use pyo3::{prelude::*, wrap_pymodule};


#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Transclusion>()?;
    m.add_class::<Entity>()?;

    Ok(())
}
