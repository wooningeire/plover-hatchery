
use super::super::{
    def_items::{
        Keysymbol,
        Sopheme,
        SophemeSeq,
        Def,
    },
    view::{
        DefViewItemRef,
        DefViewErr,
    },
    py::{
        PyDefDict,
        PyDefViewCursor,
    },
};

use pyo3::{exceptions::{PyException, PyTypeError}, prelude::*, types::PyTuple};

#[pyclass]
#[pyo3(name = "DefView")]
pub struct PyDefView {
    #[pyo3(get)] pub defs: Py<PyDefDict>,
    #[pyo3(get)] pub root_def: Py<Def>,
    pub first_consonant_cur: Option<Vec<usize>>,
    pub last_consonant_cur: Option<Vec<usize>>,
    pub first_vowel_cur: Option<Vec<usize>>,
    pub last_vowel_cur: Option<Vec<usize>>,
}

impl PyDefView {
    pub fn with_rs_of<T>(py: Python, defs: Py<PyDefDict>, root_def: Py<Def>, mut func: impl FnMut(super::DefView) -> T) -> T {
        let defs = defs.borrow(py);
        let root_def = root_def.borrow(py);
        let view_rs = super::DefView::new_ref(&defs.dict, &root_def);

        func(view_rs)
    }

    pub fn with_rs<T>(&self, py: Python, mut func: impl FnMut(super::DefView) -> T) -> T {
        let defs = self.defs.borrow(py);
        let root_def = self.root_def.borrow(py);
        let view_rs = super::DefView::new_ref(&defs.dict, &root_def);

        func(view_rs)
    }

    pub fn with_rs_result<T>(&self, py: Python, mut func: impl FnMut(super::DefView) -> Result<T, DefViewErr>) -> Result<T, PyErr> {
        self.with_rs(py, func)
            .map_err(|err| PyException::new_err(err.message()))
    }
}

#[pymethods]
impl PyDefView {
    #[new]
    pub fn new(defs: Py<PyDefDict>, root_def: Py<Def>, py: Python) -> Result<Self, PyErr> {
        PyDefView::with_rs_of(py, defs.clone_ref(py), root_def.clone_ref(py), |view_rs| {
            Ok(PyDefView {
                defs: defs.clone_ref(py),
                root_def: root_def.clone_ref(py),

                first_consonant_cur: match view_rs.first_consonant_cur().map_err(|err| err.as_pyerr())? {
                    Some(cur) => Some(cur.index_stack()),

                    None => None,
                },
                last_consonant_cur: match view_rs.last_consonant_cur().map_err(|err| err.as_pyerr())? {
                    Some(cur) => Some(cur.index_stack()),

                    None => None,
                },
                first_vowel_cur: match view_rs.first_vowel_cur().map_err(|err| err.as_pyerr())? {
                    Some(cur) => Some(cur.index_stack()),

                    None => None,
                },
                last_vowel_cur: match view_rs.last_vowel_cur().map_err(|err| err.as_pyerr())? {
                    Some(cur) => Some(cur.index_stack()),

                    None => None,
                },
            })
        })
    }

    pub fn collect_sophemes(&self, py: Python) -> Result<SophemeSeq, PyErr> {
        self.with_rs_result(py, |view_rs| view_rs.collect_sophemes())
    }


    pub fn translation(&self, py: Python) -> Result<String, PyErr> {
        self.with_rs_result(py, |view_rs| view_rs.translation())
    }


    pub fn foreach(pyself: Py<Self>, callable: PyObject, py: Python) -> Result<(), PyErr> {
        pyself.borrow(py).with_rs_result(py, |view_rs| {
            view_rs.foreach(|_, cur| {
                _ = callable.call(py, (PyDefViewCursor::of(pyself.clone_ref(py), &cur),), None);
            })
        })
    }

    pub fn foreach_keysymbol(pyself: Py<Self>, callable: PyObject, py: Python) -> Result<(), PyErr> {
        pyself.borrow(py).with_rs_result(py, |view_rs| {
            view_rs.foreach(|item_ref, cur| {
                match item_ref {
                    super::DefViewItemRef::Keysymbol(keysymbol) => {
                        _ = callable.call(py, (PyDefViewCursor::of(pyself.clone_ref(py), &cur), keysymbol.clone()), None);
                    },

                    _ => {},
                }
            })
        })
    }

    #[getter]
    pub fn first_consonant_cur<'py>(&self, py: Python<'py>) -> Result<Option<Bound<'py, PyTuple>>, PyErr> {
        Ok(match &self.first_consonant_cur {
            Some(cur) => Some(PyTuple::new(py, cur)?),

            None => None,
        })
    }

    #[getter]
    pub fn last_consonant_cur<'py>(&self, py: Python<'py>) -> Result<Option<Bound<'py, PyTuple>>, PyErr> {
        Ok(match &self.last_consonant_cur {
            Some(cur) => Some(PyTuple::new(py, cur)?),

            None => None,
        })
    }

    #[getter]
    pub fn first_vowel_cur<'py>(&self, py: Python<'py>) -> Result<Option<Bound<'py, PyTuple>>, PyErr> {
        Ok(match &self.first_vowel_cur {
            Some(cur) => Some(PyTuple::new(py, cur)?),

            None => None,
        })
    }

    #[getter]
    pub fn last_vowel_cur<'py>(&self, py: Python<'py>) -> Result<Option<Bound<'py, PyTuple>>, PyErr> {
        Ok(match &self.last_vowel_cur {
            Some(cur) => Some(PyTuple::new(py, cur)?),

            None => None,
        })
    }
}


#[pyclass]
#[pyo3(name = "DefViewItem")]
pub enum PyDefViewItem {
    Keysymbol(Keysymbol),
    Sopheme(Sopheme),
    Def(Def),
}

impl PyDefViewItem {
    pub fn of(item_ref: DefViewItemRef) -> PyDefViewItem {
        match item_ref {
            DefViewItemRef::Keysymbol(keysymbol) => PyDefViewItem::Keysymbol(keysymbol.clone()),

            DefViewItemRef::Sopheme(sopheme) => PyDefViewItem::Sopheme(sopheme.clone()),

            DefViewItemRef::Def(def) => PyDefViewItem::Def(def.clone()),

            DefViewItemRef::Entities(seq, varname) => PyDefViewItem::Def(Def::of(seq.clone(), varname)),
        }
    }
}

#[pymethods]
impl PyDefViewItem {
    pub fn keysymbol(&self) -> Result<Keysymbol, PyErr> {
        match self {
            PyDefViewItem::Keysymbol(keysymbol) => Ok(keysymbol.clone()),
            
            _ => Err(PyTypeError::new_err("not a keysymbol")),
        }
    }

    pub fn sopheme(&self) -> Result<Sopheme, PyErr> {
        match self {
            PyDefViewItem::Sopheme(sopheme) => Ok(sopheme.clone()),
            
            _ => Err(PyTypeError::new_err("not a sopheme")),
        }
    }


    #[getter]
    pub fn n_children(&self) -> usize {
        match self {
            PyDefViewItem::Keysymbol(_) => 0,

            PyDefViewItem::Sopheme(sopheme) => sopheme.keysymbols.len(),

            PyDefViewItem::Def(def) => def.entities.len(),
        }
    } 
}
