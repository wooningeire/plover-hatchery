use crate::defs::{
    py, Def, DefView, DefViewCursor, DefViewItemRef, Entity, Keysymbol, RawableEntity, Sopheme
};

use pyo3::{exceptions::PyException, prelude::*};

#[pyfunction]
pub fn optionalize_keysymbols(view: Py<py::DefView>, condition: PyObject, py: Python<'_>) -> Result<Def, PyErr> {
    view.borrow(py).with_rs(py, |view_rs| {
        let mut cur = DefViewCursor::of_view_at_start(&view_rs);

        map_def(&view_rs.root().def_ref().varname, &view_rs, view.clone_ref(py), &mut cur, &condition, py)
    })
}

fn map_def<'a>(varname: &str, view: &DefView<'a>, pyview: Py<py::DefView>, cur: &mut DefViewCursor<'a, '_>, condition: &PyObject, py: Python<'_>) -> Result<Def, PyErr> {
    let mut new_def = Def::new(vec![], varname.to_string());

    let level = cur.stack.len() - 1;

    while let Some(child) = cur.stack[level].next(view.defs()).map_err(PyException::new_err)? {
        if let Err(msg) = cur.step_in_at_start().unwrap() {
            return Err(PyException::new_err(msg));
        }

        new_def.rawables.push(match child {
            DefViewItemRef::Def(ref def) => RawableEntity::RawDef(map_def(&def.varname, &view, pyview.clone_ref(py), cur, condition, py)?),

            DefViewItemRef::EntitySeq(_, varname) => RawableEntity::RawDef(map_def(&varname, &view, pyview.clone_ref(py), cur, condition, py)?),

            DefViewItemRef::Sopheme(sopheme) => RawableEntity::Entity(Entity::Sopheme(map_sopheme(&sopheme.chars, &view, pyview.clone_ref(py), cur, condition, py)?)),

            _ => return Err(PyException::new_err("malformed definition")),
        });

        cur.step_out();
    }

    Ok(new_def)
}


fn map_sopheme<'a>(chars: &str, view: &DefView<'a>, pyview: Py<py::DefView>, cur: &mut DefViewCursor<'a, '_>, condition: &PyObject, py: Python<'_>) -> Result<Sopheme, PyErr> {
    let mut new_sopheme = Sopheme::new(chars.to_string(), vec![]);

    let level = cur.stack.len() - 1;

    while let Some(child) = cur.stack[level].next(view.defs()).map_err(PyException::new_err)? {
        if let Err(msg) = cur.step_in_at_start().unwrap() {
            return Err(PyException::new_err(msg));
        }

        new_sopheme.keysymbols.push(match child {
            DefViewItemRef::Keysymbol(keysymbol) => map_keysymbol(keysymbol, pyview.clone_ref(py), cur, condition, py)?,

            _ => return Err(PyException::new_err("malformed definition")),
        });

        cur.step_out();
    }

    Ok(new_sopheme)
}

fn map_keysymbol<'a>(keysymbol: &Keysymbol, pyview: Py<py::DefView>, cur: &mut DefViewCursor<'a, '_>, condition: &PyObject, py: Python<'_>) -> Result<Keysymbol, PyErr> {
    let obj = condition.call(py, (py::DefViewCursor::of(pyview, cur),), None)?;

    if obj.extract(py)? {
        Ok(Keysymbol::new_with_known_base_symbol(
            keysymbol.symbol().to_string(),
            keysymbol.base_symbol().to_string(),
            keysymbol.stress(),
            true,
        ))
    } else {
        Ok(keysymbol.clone())
    }
}
