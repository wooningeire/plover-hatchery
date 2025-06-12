use pyo3::{prelude::*, wrap_pyfunction};

mod defs;
use defs::{
    Def,
    py::{
        DefDict,
        DefView,
        DefViewCursor,
        DefViewItem,
    },
    SophemeSeq,
    Entity,
    Sopheme,
    Keysymbol,
    Transclusion,
};

mod pipes;
use pipes::{
    optionalize_keysymbols,
    add_diphthong_keysymbols,
};


#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Def>()?;
    m.add_class::<DefDict>()?;
    m.add_class::<DefView>()?;
    m.add_class::<DefViewCursor>()?;
    m.add_class::<DefViewItem>()?;
    m.add_class::<SophemeSeq>()?;
    m.add_class::<Entity>()?;
    m.add_class::<Sopheme>()?;
    m.add_class::<Keysymbol>()?;
    m.add_class::<Transclusion>()?;

    m.add_function(wrap_pyfunction!(optionalize_keysymbols, m)?)?;
    m.add_function(wrap_pyfunction!(add_diphthong_keysymbols, m)?)?;

    Ok(())
}
