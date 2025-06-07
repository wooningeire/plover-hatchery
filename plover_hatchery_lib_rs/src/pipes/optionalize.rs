use crate::defs::{
    Def,
    DefView,
    DefViewCursor,
    py,
};

use pyo3::{prelude::*};

#[pyfunction]
pub fn optionalize_keysymbols(view: Py<py::DefView>, condition: PyObject, py: Python<'_>) -> Result<Def, PyErr> {
    view.borrow(py).with_rs_result(py, |view_rs| {
        let mut cur = DefViewCursor::of_view(&view_rs);

        map_def(&view_rs.root().def_ref(), &view_rs, &mut cur)
    })
}

fn map_def<'a>(def: &Def, view: &DefView<'a>, cur: &mut DefViewCursor<'a>) -> Result<Def, &'static str> {
    let new_def = Def::empty(def.varname.clone());

    for child in cur.stack.last_mut().unwrap().iter_mut(view.defs()) {
        // match child? {
            
        // }
    }

    Ok(new_def)
}