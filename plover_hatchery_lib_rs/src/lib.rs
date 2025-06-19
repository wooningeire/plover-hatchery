use pyo3::{prelude::*, wrap_pyfunction};

mod defs;
use defs::{
    Def,
    py::{
        PyDefDict,
        PyDefView,
        PyDefViewCursor,
        PyDefViewItem,
        py_parse_entry_definition,
        py_parse_sopheme_seq,
        py_parse_keysymbol_seq,
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

mod morphology;
use morphology::{
    AffixKey,
};


#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Def>()?;
    m.add_class::<PyDefDict>()?;
    m.add_class::<PyDefView>()?;
    m.add_class::<PyDefViewCursor>()?;
    m.add_class::<PyDefViewItem>()?;
    m.add_class::<SophemeSeq>()?;
    m.add_class::<Entity>()?;
    m.add_class::<Sopheme>()?;
    m.add_class::<Keysymbol>()?;
    m.add_class::<Transclusion>()?;

    m.add_function(wrap_pyfunction!(optionalize_keysymbols, m)?)?;
    m.add_function(wrap_pyfunction!(add_diphthong_keysymbols, m)?)?;

    m.add_class::<AffixKey>()?;

    m.add_function(wrap_pyfunction!(py_parse_entry_definition, m)?)?;
    m.add_function(wrap_pyfunction!(py_parse_sopheme_seq, m)?)?;
    m.add_function(wrap_pyfunction!(py_parse_keysymbol_seq, m)?)?;

    Ok(())
}
