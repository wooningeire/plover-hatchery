
use pyo3::{prelude::*, exceptions::PyException};

use super::*;



#[pyclass]
pub struct DefDict {
    dict: Box<super::DefDict>,
}

#[pymethods]
impl DefDict {
    #[new]
    pub fn new() -> Self {
        DefDict {
            dict: Box::new(super::DefDict::new()),
        }
    }

    pub fn add(&mut self, varname: String, seq: EntitySeq) {
        self.dict.add(varname, seq);
    }

    pub fn get_def(&self, varname: &str) -> Option<Def> {
        self.dict.get_def(varname)
    }

    pub fn foreach_key(&self, py: Python<'_>, callable: PyObject) {
        for varname in self.dict.entries.keys() {
            _ = callable.call(py, (varname.to_string(),), None);
        }
    }
}


// #[pyclass]
// #[derive(Clone)]
// pub enum DefViewItem {
//     Root(Definition),
//     Rawable(RawableEntity),
//     Entity(Entity),
//     Keysymbol(Keysymbol),
// }

// impl DefViewItem {
//     pub fn of(item: super::DefViewItem) -> DefViewItem {
//         match item {
//             super::DefViewItem::Root() => ,
//             super::DefViewItem::Rawable(rawable) => DefViewItem::Rawable(()),
//             super::DefViewItem::Entity(entity) => DefViewItem::Entity(entity.clone()),
//             super::DefViewItem::Keysymbol(keysymbol) => DefViewItem::Keysymbol(keysymbol.clone()),
//         }
//     }
// }


// #[pyclass(get_all)]
// #[derive(Clone)]
// pub struct StackItem {
//     index: usize,
//     item: DefViewItem,
// }

// impl StackItem {
//     pub fn of(item: super::StackItem) -> StackItem {
//         StackItem {
//             index: item.index,
//             item: DefViewItem::of(item.item),
//         }
//     }
// }


// #[pyclass]
// #[derive(Clone)]
// pub enum StepData {
//     In(StackItem),
//     Over(StackItem),
//     Out(),
// }

// impl StepData {
//     pub fn of(data: super::StepData) -> StepData {
//         match data {
//             super::StepData::In(item) => StepData::In(StackItem::of(item)),
//             super::StepData::Over(item) => StepData::Over(StackItem::of(item)),
//             super::StepData::Out => StepData::Out(),
//         }
//     }
// }


#[pyclass(get_all)]
pub struct DefView {
    pub defs: Py<DefDict>,
    pub root_def: Py<Def>,
}

impl DefView {
    fn with_rs<T>(&self, py: Python<'_>, func: impl Fn(super::DefView) -> T) -> T {
        let defs = self.defs.borrow(py);
        let root_def = self.root_def.borrow(py);
        let view_rs = super::DefView::new_ref(&defs.dict, &root_def);

        func(view_rs)
    }

    fn with_rs_result<T>(&self, py: Python<'_>, func: impl Fn(super::DefView) -> Result<T, &'static str>) -> Result<T, PyErr> {
        self.with_rs(py, func)
            .map_err(|msg| PyException::new_err(msg))
    }
}

#[pymethods]
impl DefView {
    #[new]
    pub fn new(defs: Py<DefDict>, root_def: Py<Def>) -> Self {
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
            let mut cursor = super::DefViewCursor::of_view(&view_rs);

            while let Some(item_ref) = cursor.step() {
                match item_ref? {
                    super::DefViewItemRef::Keysymbol(keysymbol) => {
                        _ = callable.call(py, (DefViewCursor::of(pyself.clone_ref(py), &cursor), keysymbol.clone()), None);
                    },

                    _ => {},
                }
            }

            Ok(())
        })
    }

    // pub fn map_keysymbols(pyself: Py<Self>, callable: PyObject, py: Python<'_>) -> Def {
    //     let view = pyself.borrow(py);

    //     let mut new_def = super::Def::empty(view.root_def.borrow(py).varname.clone());

    //     view.with_rs(py, |view_rs| {
    //         let mut cursor = super::DefViewCursor::of_view(&view_rs);

    //         let mut new_item_stack: Vec<super::DefViewItemRef> = vec![];

    //         while let Some(data) = cursor.step() {
    //             match data {
    //                 super::StepData::In(item) => match item.item_ref {
    //                     super::DefViewItemRef::
    //                 },

    //                 super::StepData::Over(_, item) => call_keysymbol_callback(item, &cursor, &pyself, &callable, py),
    //             }
    //         }
    //     });

    //     new_def
    // }
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


#[pyclass(get_all)]
pub struct DefViewCursor {
    view: Py<DefView>,
    index_stack: Vec<usize>,
}

impl DefViewCursor {
    pub fn of(view: Py<DefView>, cursor: &super::DefViewCursor) -> DefViewCursor {
        DefViewCursor {
            view,
            index_stack: cursor.stack.iter()
                .map(|iter| iter.index().unwrap_or(0))
                .collect::<Vec<_>>(),
        }
    }
}

#[pymethods]
impl DefViewCursor {
    #[new]
    pub fn new(view: Py<DefView>, index_stack: Vec<usize>) -> DefViewCursor {
        DefViewCursor {
            view,
            index_stack,
        }
    }


    pub fn tip(&self, py: Python<'_>) -> Result<Option<DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(match view_rs.read(&self.index_stack) {
                Some(item_ref) => DefViewItem::of(item_ref?, &self.view.borrow(py).defs.borrow(py).dict),

                None => None,
            })
        })
    }

    pub fn nth(&self, level: usize, py: Python<'_>) -> Result<Option<DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            Ok(match view_rs.read(&self.index_stack[..level]) {
                Some(item_ref) => DefViewItem::of(item_ref?, &self.view.borrow(py).defs.borrow(py).dict),

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