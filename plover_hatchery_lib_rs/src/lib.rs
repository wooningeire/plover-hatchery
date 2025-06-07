use pyo3::{prelude::*, wrap_pyfunction};

mod defs;
use defs::{
    EntitySeq,
    Def,
    py::{
        DefDict,
        DefView,
        DefViewCursor,
        DefViewItem,
    },
    SophemeSeq,
    Entity,
    RawableEntity,
    Sopheme,
    Keysymbol,
    Transclusion,
};

mod pipes;
use pipes::{
    optionalize_keysymbols,
};


#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<EntitySeq>()?;
    m.add_class::<Def>()?;
    m.add_class::<DefDict>()?;
    m.add_class::<DefView>()?;
    m.add_class::<DefViewCursor>()?;
    m.add_class::<DefViewItem>()?;
    m.add_class::<SophemeSeq>()?;
    m.add_class::<Entity>()?;
    m.add_class::<RawableEntity>()?;
    m.add_class::<Sopheme>()?;
    m.add_class::<Keysymbol>()?;
    m.add_class::<Transclusion>()?;

    m.add_function(wrap_pyfunction!(optionalize_keysymbols, m)?)?;

    Ok(())
}
