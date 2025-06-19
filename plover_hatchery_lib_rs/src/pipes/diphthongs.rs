use super::map_def_items::map_def;

use crate::defs::{
    py::{
        PyDefView,
        PyDefViewCursor,
    },
    Def,
    Keysymbol,
    DefViewCursor,
};

use pyo3::prelude::*;

#[pyfunction]
pub fn add_diphthong_keysymbols(view: Py<PyDefView>, map_keysymbols: PyObject, py: Python) -> Result<Def, PyErr> {
    view.borrow(py).with_rs(py, |view_rs| {
        let mut cur = DefViewCursor::of_view_at_start(&view_rs);

        map_def(
            &view_rs.root().def_ref().varname,
            &mut cur,
            &|vec, keysymbol, cur| {
                let obj = map_keysymbols.call(py, (PyDefViewCursor::of(view.clone_ref(py), cur),), None)?;

                vec.extend(obj.extract::<Vec<Keysymbol>>(py)?);
                vec.push(keysymbol.clone());

                Ok(())
            },
        )
    })
}
