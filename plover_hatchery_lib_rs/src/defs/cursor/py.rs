use pyo3::prelude::*;

use super::super::{
    py,
};


#[pyclass(get_all)]
pub struct DefViewCursor {
    view: Py<py::DefView>,
    index_stack: Vec<usize>,
}

impl DefViewCursor {
    pub fn of(view: Py<py::DefView>, cursor: &super::DefViewCursor) -> DefViewCursor {
        DefViewCursor {
            view,
            index_stack: cursor.index_stack(),
        }
    }
}

#[pymethods]
impl DefViewCursor {
    #[new]
    pub fn new(view: Py<py::DefView>, index_stack: Vec<usize>) -> DefViewCursor {
        DefViewCursor {
            view,
            index_stack,
        }
    }


    pub fn tip(&self, py: Python<'_>) -> Result<Option<py::DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(match view_rs.read(&self.index_stack) {
                Some(item_ref) => py::DefViewItem::of(item_ref?, &self.view.borrow(py).defs.borrow(py).dict),

                None => None,
            })
        })
    }

    pub fn nth(&self, level: usize, py: Python<'_>) -> Result<Option<py::DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(match view_rs.read(&self.index_stack[..level]) {
                Some(item_ref) => py::DefViewItem::of(item_ref?, &self.view.borrow(py).defs.borrow(py).dict),

                None => None,
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