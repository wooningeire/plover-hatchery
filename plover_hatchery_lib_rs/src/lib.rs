use pyo3::{prelude::*, wrap_pymodule};

mod definition;
use definition::{
    Definition,
    DefinitionDictionary,
    Entity,
    Sopheme,
    Keysymbol,
    Transclusion,
};


#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Definition>()?;
    m.add_class::<DefinitionDictionary>()?;
    m.add_class::<Entity>()?;
    m.add_class::<Sopheme>()?;
    m.add_class::<Keysymbol>()?;
    m.add_class::<Transclusion>()?;

    Ok(())
}
