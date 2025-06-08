use pyo3::{exceptions::{PyException, PyKeyError, PyTypeError}, prelude::*};

use super::super::{
    DefViewItemRef,
    DefView,
    py,
};


#[pyclass(get_all)]
pub struct DefViewCursor {
    view: Py<py::DefView>,
    index_stack: Vec<usize>,
}

impl py::DefViewCursor {
    pub fn of(view: Py<py::DefView>, cursor: &super::DefViewCursor) -> py::DefViewCursor {
        py::DefViewCursor {
            view,
            index_stack: cursor.index_stack(),
        }
    }

    pub fn with_rs<T>(&self, view_rs: &DefView, func: impl Fn(super::DefViewCursor) -> T) -> Result<T, PyErr> {
        let cursor_rs = super::DefViewCursor::with_index_stack(view_rs, self.index_stack.clone().into_iter().map(Some))
            .map_err(PyException::new_err)?;

        Ok(func(cursor_rs))
    }

    pub fn with_rs_result<T>(&self, view_rs: &DefView, func: impl Fn(super::DefViewCursor) -> Result<T, &'static str>) -> Result<T, PyErr> {
        self.with_rs(view_rs, func)?
            .map_err(PyException::new_err)
    }
}

#[pymethods]
impl py::DefViewCursor {
    #[new]
    pub fn new(view: Py<py::DefView>, index_stack: Vec<usize>) -> py::DefViewCursor {
        py::DefViewCursor {
            view,
            index_stack,
        }
    }

    pub fn tip(&self, py: Python<'_>) -> Result<py::DefViewItem, PyErr> {
        self.maybe_tip(py)?.ok_or(PyTypeError::new_err("cursor is not pointing to anything"))
    }

    pub fn maybe_tip(&self, py: Python<'_>) -> Result<Option<py::DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(view_rs.read(&self.index_stack)?.map(py::DefViewItem::of))
        })
    }

    pub fn nth(&self, level: usize, py: Python<'_>) -> Result<py::DefViewItem, PyErr> {
        self.maybe_nth(level, py)?.ok_or(PyKeyError::new_err("cursor has nothing at this level"))
    }

    pub fn maybe_nth(&self, level: usize, py: Python<'_>) -> Result<Option<py::DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(view_rs.read(&self.index_stack[..level])?.map(py::DefViewItem::of))
        })
    }

    pub fn prev_keysymbol_loc(&self, py: Python<'_>) -> Result<Option<py::DefViewCursor>, PyErr> {
        self.view.borrow(py).with_rs(py, |view_rs| {
            self.with_rs_result(&view_rs, |cursor_rs| {
                Ok(
                    view_rs.first_index_before(
                        cursor_rs,
                        |item_ref| match item_ref {
                            DefViewItemRef::Keysymbol(_) => true,

                            _ => false,
                        },
                    )?
                        .map(|cur| py::DefViewCursor::of(self.view.clone_ref(py), &cur))
                )
            })
        })
    }

    pub fn next_keysymbol_loc(&self, py: Python<'_>) -> Result<Option<py::DefViewCursor>, PyErr> {
        self.view.borrow(py).with_rs(py, |view_rs| {
            self.with_rs_result(&view_rs, |cursor_rs| {
                Ok(
                    view_rs.first_index_after(
                        cursor_rs,
                        |item_ref| match item_ref {
                            DefViewItemRef::Keysymbol(_) => true,

                            _ => false,
                        },
                    )?
                        .map(|cur| py::DefViewCursor::of(self.view.clone_ref(py), &cur))
                )
            })
        })
    }

    #[getter]
    pub fn stack_len(&self) -> usize {
        self.index_stack.len()
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.index_stack)
    }
}