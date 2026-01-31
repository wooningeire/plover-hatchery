use pyo3::{exceptions::{PyException, PyKeyError}, prelude::*, types::PyTuple};

use crate::defs::cursor::seq_less_than;

use super::super::{
    py::{
        PyDefView,
        PyDefViewItem,
    },
    view::DefViewErr,
};


#[pyclass]
#[pyo3(name = "DefViewCursor")]
pub struct PyDefViewCursor {
    #[pyo3(get)] pub view: Py<PyDefView>,
    index_stack: Vec<usize>,
}

impl Clone for PyDefViewCursor {
    fn clone(&self) -> Self {
        Python::with_gil(|py| PyDefViewCursor {
            view: self.view.clone_ref(py),
            index_stack: self.index_stack.clone(),
        })
    }
}

impl PyDefViewCursor {
    pub fn of(view: Py<PyDefView>, cursor: &super::DefViewCursor) -> PyDefViewCursor {
        PyDefViewCursor {
            view,
            index_stack: cursor.index_stack(),
        }
    }

    pub fn with_rs<T>(&self, py: Python, func: impl Fn(super::DefViewCursor) -> T) -> Result<T, PyErr> {
        self.view.borrow(py).with_rs(py, |view_rs| {
            let cursor_rs = super::DefViewCursor::with_index_stack(&view_rs, self.index_stack.clone().into_iter().map(Some))
                .map_err(|err| err.as_pyerr())?
                .ok_or(DefViewErr::UnexpectedNone.as_pyerr())?;

            Ok(func(cursor_rs))
        })
    }

    pub fn with_rs_result<T>(&self, py: Python, func: impl Fn(super::DefViewCursor) -> Result<T, DefViewErr>) -> Result<T, PyErr> {
        self.with_rs(py, func)?
            .map_err(|err| err.as_pyerr())
    }

    pub fn occurs_before(&self, maybe_cur: &Option<Vec<usize>>) -> bool {
        match maybe_cur {
            Some(cur) => seq_less_than(self.index_stack.iter(), cur.iter()),

            None => true,
        }
    }

    pub fn occurs_after(&self, maybe_cur: &Option<Vec<usize>>) -> bool {
        match maybe_cur {
            Some(cur) => seq_less_than(cur.iter(), self.index_stack.iter()),

            None => true,
        }
    }
}

#[pymethods]
impl PyDefViewCursor {
    #[new]
    pub fn new(view: Py<PyDefView>, index_stack: Vec<usize>) -> PyDefViewCursor {
        PyDefViewCursor {
            view,
            index_stack,
        }
    }

    #[getter]
    pub fn index_stack<'py>(&self, py: Python<'py>) -> Result<Bound<'py, PyTuple>, PyErr> {
        PyTuple::new(py, &self.index_stack)
    }

    pub fn tip(&self, py: Python) -> Result<PyDefViewItem, PyErr> {
        self.maybe_tip(py)?.ok_or(PyException::new_err("cursor is not pointing to anything"))
    }

    pub fn maybe_tip(&self, py: Python) -> Result<Option<PyDefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(view_rs.get(&self.index_stack)?.map(PyDefViewItem::of))
        })
    }

    pub fn nth(&self, level: usize, py: Python) -> Result<PyDefViewItem, PyErr> {
        self.maybe_nth(level, py)?.ok_or(PyKeyError::new_err("cursor has nothing at this level"))
    }

    pub fn maybe_nth(&self, level: usize, py: Python) -> Result<Option<PyDefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(view_rs.get(&self.index_stack[..level])?.map(PyDefViewItem::of))
        })
    }

    pub fn prev_keysymbol_cur(&self, py: Python) -> Result<Option<PyDefViewCursor>, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.prev_keysymbol_cur()
                .map(|result| result.map(|cur| PyDefViewCursor::of(self.view.clone_ref(py), &cur)))
        })
    }

    pub fn next_keysymbol_cur(&self, py: Python) -> Result<Option<PyDefViewCursor>, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.next_keysymbol_cur()
                .map(|result| result.map(|cur| PyDefViewCursor::of(self.view.clone_ref(py), &cur)))
        })
    }

    #[getter]
    pub fn stack_len(&self) -> usize {
        self.index_stack.len()
    }

    pub fn __repr__(&self) -> String {
        format!("{:?}", self.index_stack)
    }

    pub fn occurs_before_first_consonant(&self, py: Python) -> bool {
        self.occurs_before(&self.view.borrow(py).first_consonant_cur)
    }

    pub fn occurs_after_last_consonant(&self, py: Python) -> bool {
        self.occurs_after(&self.view.borrow(py).last_consonant_cur)
    }

    pub fn occurs_before_first_vowel(&self, py: Python) -> bool {
        self.occurs_before(&self.view.borrow(py).first_vowel_cur)
    }

    pub fn occurs_after_last_vowel(&self, py: Python) -> bool {
        self.occurs_after(&self.view.borrow(py).last_vowel_cur)
    }

    pub fn spelling_including_silent(&self, py: Python) -> Result<String, PyErr> {
        self.with_rs_result(py, |cursor_rs| {
            cursor_rs.spelling_including_silent()
        })
    }
}