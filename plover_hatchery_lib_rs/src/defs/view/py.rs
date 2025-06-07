
use super::super::{
    def_items::{
        Keysymbol,
        Entity,
        Sopheme,
        SophemeSeq,
        RawableEntity,
    },
    def::Def,
    py,
};

use pyo3::{exceptions::PyException, prelude::*};


#[pyclass(get_all)]
pub struct DefView {
    pub defs: Py<py::DefDict>,
    pub root_def: Py<Def>,
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
}

#[pyclass]
pub enum DefViewItem {
    Keysymbol(Keysymbol),
    Sopheme(Sopheme),
    Def(Def),
}

impl DefViewItem {
    pub fn of(item_ref: super::DefViewItemRef, defs: &super::DefDict) -> Option<DefViewItem> {
        Some(match item_ref {
            super::DefViewItemRef::Keysymbol(keysymbol) => DefViewItem::Keysymbol(keysymbol.clone()),

            super::DefViewItemRef::Entity(entity) => match entity {
                Entity::Sopheme(sopheme) => DefViewItem::Sopheme(sopheme.clone()),

                Entity::Transclusion(transclusion) => DefViewItem::Def(defs.get_def(&transclusion.target_varname)?),
            },

            super::DefViewItemRef::Rawable(rawable) => match rawable {
                RawableEntity::Entity(entity) => match entity {
                    Entity::Sopheme(sopheme) => DefViewItem::Sopheme(sopheme.clone()),

                    Entity::Transclusion(transclusion) => DefViewItem::Def(defs.get_def(&transclusion.target_varname)?),
                },

                RawableEntity::RawDef(def) => DefViewItem::Def(def.clone()),
            },
            
            super::DefViewItemRef::Root(def) => DefViewItem::Def(def.clone()),
        })
    }
}

#[pymethods]
impl DefViewItem {
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
