
use super::super::{
    def_items::{
        Keysymbol,
        Sopheme,
        SophemeSeq,
        Def,
    },
    view::DefViewItemRef,
    py,
};

use pyo3::{exceptions::{PyException, PyTypeError}, prelude::*};


#[pyclass]
pub struct DefView {
    #[pyo3(get)] pub defs: Py<py::DefDict>,
    #[pyo3(get)] pub root_def: Py<Def>,
    // pub first_consonant_loc_cache: Option<Option<Vec<usize>>>,
    // pub last_consonant_loc_cache: Option<Option<Vec<usize>>>,
    // pub first_vowel_loc_cache: Option<Option<Vec<usize>>>,
    // pub last_vowel_loc_cache: Option<Option<Vec<usize>>>,
}

impl DefView {
    pub fn with_rs<T>(&self, py: Python<'_>, func: impl Fn(super::DefView) -> T) -> T {
        let defs = self.defs.borrow(py);
        let root_def = self.root_def.borrow(py);
        let view_rs = super::DefView::new_ref(&defs.dict, &root_def);

        func(view_rs)
    }

    pub fn with_rs_result<T>(&self, py: Python<'_>, func: impl Fn(super::DefView) -> Result<T, &'static str>) -> Result<T, PyErr> {
        self.with_rs(py, func)
            .map_err(|msg| PyException::new_err(msg))
    }
}

#[pymethods]
impl DefView {
    #[new]
    pub fn new(defs: Py<py::DefDict>, root_def: Py<Def>) -> Self {
        DefView {
            defs,
            root_def,
            // first_consonant_loc_cache: None,
            // last_consonant_loc_cache: None,
            // first_vowel_loc_cache: None,
            // last_vowel_loc_cache: None,
        }
    }

    pub fn collect_sophemes(&self, py: Python<'_>) -> Result<SophemeSeq, PyErr> {
        self.with_rs_result(py, |view_rs| view_rs.collect_sophemes())
    }


    pub fn translation(&self, py: Python<'_>) -> Result<String, PyErr> {
        self.with_rs_result(py, |view_rs| view_rs.translation())
    }

    pub fn foreach_keysymbol(pyself: Py<Self>, callable: PyObject, py: Python<'_>) -> Result<(), PyErr> {
        pyself.borrow(py).with_rs_result(py, |view_rs| {
            view_rs.foreach(|item_ref, cursor| {
                match item_ref {
                    super::DefViewItemRef::Keysymbol(keysymbol) => {
                        _ = callable.call(py, (py::DefViewCursor::of(pyself.clone_ref(py), &cursor), keysymbol.clone()), None);
                    },

                    _ => {},
                }
            })?;

            Ok(())
        })
    }

    #[getter]
    pub fn first_consonant_loc(&self, py: Python<'_>) -> Result<Option<Vec<usize>>, PyErr> {
        self.with_rs_result(py, |view_rs| {
            Ok(
                view_rs.first_index(|item_ref| match item_ref {
                    DefViewItemRef::Keysymbol(keysymbol) => keysymbol.is_consonant(),

                    _ => false,
                })?
                    .map(|cur| cur.index_stack())
            )
        })
    }

    #[getter]
    pub fn last_consonant_loc(&self, py: Python<'_>) -> Result<Option<Vec<usize>>, PyErr> {
        self.with_rs_result(py, |view_rs| {
            Ok(
                view_rs.last_index(|item_ref| match item_ref {
                    DefViewItemRef::Keysymbol(keysymbol) => keysymbol.is_consonant(),

                    _ => false,
                })?
                    .map(|cur| cur.index_stack())
            )
        })
    }

    #[getter]
    pub fn first_vowel_loc(&self, py: Python<'_>) -> Result<Option<Vec<usize>>, PyErr> {
        self.with_rs_result(py, |view_rs| {
            Ok(
                view_rs.first_index(|item_ref| match item_ref {
                    DefViewItemRef::Keysymbol(keysymbol) => keysymbol.is_vowel(),

                    _ => false,
                })?
                    .map(|cur| cur.index_stack())
            )
        })
    }

    #[getter]
    pub fn last_vowel_loc(&self, py: Python<'_>) -> Result<Option<Vec<usize>>, PyErr> {
        self.with_rs_result(py, |view_rs| {
            Ok(
                view_rs.last_index(|item_ref| match item_ref {
                    DefViewItemRef::Keysymbol(keysymbol) => keysymbol.is_vowel(),

                    _ => false,
                })?
                    .map(|cur| cur.index_stack())
            )
        })
    }
}

#[pyclass]
pub enum DefViewItem {
    Keysymbol(Keysymbol),
    Sopheme(Sopheme),
    Def(Def),
}

impl DefViewItem {
    pub fn of(item_ref: DefViewItemRef) -> DefViewItem {
        match item_ref {
            DefViewItemRef::Keysymbol(keysymbol) => DefViewItem::Keysymbol(keysymbol.clone()),

            DefViewItemRef::Sopheme(sopheme) => DefViewItem::Sopheme(sopheme.clone()),

            DefViewItemRef::Def(def) => DefViewItem::Def(def.clone()),

            DefViewItemRef::EntitySeq(seq, varname) => DefViewItem::Def(Def::of(seq.clone(), varname)),
        }
    }
}

#[pymethods]
impl DefViewItem {
    pub fn keysymbol(&self) -> Result<Keysymbol, PyErr> {
        match self {
            DefViewItem::Keysymbol(keysymbol) => Ok(keysymbol.clone()),
            
            _ => Err(PyTypeError::new_err("not a keysymbol")),
        }
    }

    pub fn sopheme(&self) -> Result<Sopheme, PyErr> {
        match self {
            DefViewItem::Sopheme(sopheme) => Ok(sopheme.clone()),
            
            _ => Err(PyTypeError::new_err("not a sopheme")),
        }
    }

    #[getter]
    pub fn maybe_keysymbol(&self) -> Option<Keysymbol> {
        match self {
            DefViewItem::Keysymbol(keysymbol) => Some(keysymbol.clone()),
            
            _ => None,
        }
    }

    #[getter]
    pub fn maybe_sopheme(&self) -> Option<Sopheme> {
        match self {
            DefViewItem::Sopheme(sopheme) => Some(sopheme.clone()),
            
            _ => None,
        }
    }

    #[getter]
    pub fn maybe_def(&self) -> Option<Def> {
        match self {
            DefViewItem::Def(def) => Some(def.clone()),
            
            _ => None,
        }
    }
}
