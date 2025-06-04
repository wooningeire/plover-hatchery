use pyo3::{prelude::*, wrap_pymodule};

mod definition;
use definition::{
    EntitySeq,
    Def,
    py::{
        DefDict,
        DefView,
        DefViewCursor,
    },
    SophemeSeq,
    Entity,
    RawableEntity,
    Sopheme,
    Keysymbol,
    Transclusion,
};


#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<EntitySeq>()?;
    m.add_class::<Def>()?;
    m.add_class::<DefDict>()?;
    m.add_class::<DefView>()?;
    m.add_class::<DefViewCursor>()?;
    m.add_class::<SophemeSeq>()?;
    m.add_class::<Entity>()?;
    m.add_class::<RawableEntity>()?;
    m.add_class::<Sopheme>()?;
    m.add_class::<Keysymbol>()?;
    m.add_class::<Transclusion>()?;

    Ok(())
}
