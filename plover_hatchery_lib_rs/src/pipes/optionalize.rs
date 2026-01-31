use super::map_def_items::map_def;

use crate::defs::{
    py::{
        PyDefView,
        PyDefViewCursor,
    },
    Def,
    DefViewCursor,
    Keysymbol,
};

use pyo3::prelude::*;

#[pyfunction]
pub fn optionalize_keysymbols(view: Py<PyDefView>, condition: Py<PyAny>, py: Python) -> Result<Def, PyErr> {
    view.borrow(py).with_rs(py, |view_rs| {
        let mut cur = DefViewCursor::of_view_at_start(&view_rs);

        map_def(
            &view_rs.root().def_ref().varname,
            &mut cur,
            &|vec, keysymbol, cur| {
                let obj = condition.call(py, (PyDefViewCursor::of(view.clone_ref(py), cur),), None)?;

                vec.push(
                    if obj.extract(py)? {
                        Keysymbol::new_with_known_base_symbol(
                            keysymbol.symbol().to_string(),
                            keysymbol.base_symbol().to_string(),
                            keysymbol.stress(),
                            true,
                        )
                    } else {
                        keysymbol.clone()
                    }
                );

                Ok(())
            },
        )
    })
}
