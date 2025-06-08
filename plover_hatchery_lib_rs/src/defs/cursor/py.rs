use pyo3::{exceptions::{PyException, PyKeyError}, prelude::*, types::PyTuple};

use super::super::{
    py,
    view::DefViewErr,
};


#[pyclass]
pub struct DefViewCursor {
    #[pyo3(get)] view: Py<py::DefView>,
    index_stack: Vec<usize>,
}

impl py::DefViewCursor {
    pub fn of(view: Py<py::DefView>, cursor: &super::DefViewCursor) -> py::DefViewCursor {
        py::DefViewCursor {
            view,
            index_stack: cursor.index_stack(),
        }
    }

    pub fn with_rs<T>(&self, py: Python<'_>, func: impl Fn(super::DefViewCursor) -> T) -> Result<T, PyErr> {
        self.view.borrow(py).with_rs(py, |view_rs| {
            let cursor_rs = super::DefViewCursor::with_index_stack(&view_rs, self.index_stack.clone().into_iter().map(Some))
                .map_err(|err| err.as_pyerr())?
                .ok_or(DefViewErr::UnexpectedNone.as_pyerr())?;

            Ok(func(cursor_rs))
        })
    }

    pub fn with_rs_result<T>(&self, py: Python<'_>, func: impl Fn(super::DefViewCursor) -> Result<T, DefViewErr>) -> Result<T, PyErr> {
        self.with_rs(py, func)?
            .map_err(|err| err.as_pyerr())
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

    #[getter]
    pub fn index_stack<'py>(&self, py: Python<'py>) -> Result<Bound<'py, PyTuple>, PyErr> {
        PyTuple::new(py, &self.index_stack)
    }

    pub fn tip(&self, py: Python<'_>) -> Result<py::DefViewItem, PyErr> {
        self.maybe_tip(py)?.ok_or(PyException::new_err("cursor is not pointing to anything"))
    }

    pub fn maybe_tip(&self, py: Python<'_>) -> Result<Option<py::DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(view_rs.get(&self.index_stack)?.map(py::DefViewItem::of))
        })
    }

    pub fn nth(&self, level: usize, py: Python<'_>) -> Result<py::DefViewItem, PyErr> {
        self.maybe_nth(level, py)?.ok_or(PyKeyError::new_err("cursor has nothing at this level"))
    }

    pub fn maybe_nth(&self, level: usize, py: Python<'_>) -> Result<Option<py::DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(view_rs.get(&self.index_stack[..level])?.map(py::DefViewItem::of))
        })
    }

    pub fn prev_keysymbol_cur(&self, py: Python<'_>) -> Result<Option<py::DefViewCursor>, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.prev_keysymbol_cur()
                .map(|result| result.map(|cur| py::DefViewCursor::of(self.view.clone_ref(py), &cur)))
        })
    }

    pub fn next_keysymbol_cur(&self, py: Python<'_>) -> Result<Option<py::DefViewCursor>, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.next_keysymbol_cur()
                .map(|result| result.map(|cur| py::DefViewCursor::of(self.view.clone_ref(py), &cur)))
        })
    }

    #[getter]
    pub fn stack_len(&self) -> usize {
        self.index_stack.len()
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.index_stack)
    }

    pub fn occurs_before_first_consonant(&self, py: Python<'_>) -> Result<bool, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.occurs_before_first_consonant()
        })
    }

    pub fn occurs_after_last_consonant(&self, py: Python<'_>) -> Result<bool, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.occurs_after_last_consonant()
        })
    }

    pub fn occurs_before_first_vowel(&self, py: Python<'_>) -> Result<bool, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.occurs_before_first_vowel()
        })
    }

    pub fn occurs_after_last_vowel(&self, py: Python<'_>) -> Result<bool, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.occurs_after_last_vowel()
        })
    }
}