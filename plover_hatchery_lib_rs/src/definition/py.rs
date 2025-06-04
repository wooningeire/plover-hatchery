
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
    defs: Py<DefDict>,
    root_def: Py<Def>,
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


    pub fn foreach_step(&self, py: Python<'_>, callable: PyObject) {
        self.with_rs(py, |view_rs| {
            let mut cursor = super::DefViewCursor::new(&view_rs);

            while let Some(_) = cursor.step() {
                _ = callable.call(py, (/* StepData::of(data) */), None);
            }
        });
    }

    pub fn foreach_keysymbol(pyself: Py<Self>, callable: PyObject, py: Python<'_>) {
        pyself.borrow(py).with_rs(py, |view_rs| {
            let mut cursor = super::DefViewCursor::new(&view_rs);

            while let Some(data) = cursor.step() {
                match data {
                    super::StepData::In(item) => call_keysymbol_callback(item, &cursor, &pyself, &callable, py),

                    super::StepData::Over(_, item) => call_keysymbol_callback(item, &cursor, &pyself, &callable, py),
                }
            }
        });
    }
}

fn call_keysymbol_callback(item: super::StackItem, cursor: &super::DefViewCursor, pyself: &Py<DefView>, callable: &PyObject, py: Python<'_>) {
    if let super::DefViewItem::Keysymbol(keysymbol) = item.item {
        _ = callable.call(py, (DefViewCursor::of(pyself.clone_ref(py), &cursor), keysymbol.clone()), None);

        // if let Some(parent) = cursor.stack.get(cursor.stack.len() - 2) {
        //     if let Some(sopheme) = parent.item.get_if_sopheme() {
                // _ = callable.call(py, (DefViewCursor::of(pyself.clone_ref(py), &cursor), sopheme.clone(), keysymbol.clone()), None);
        //     }
        // }
    }
}


#[pyclass]
pub enum DefViewItem {
    Keysymbol(Keysymbol),
    Sopheme(Sopheme),
    NotImplemented(),
}

impl DefViewItem {
    pub fn of(item: super::DefViewItem) -> DefViewItem {
        match item {
            super::DefViewItem::Keysymbol(keysymbol) => DefViewItem::Keysymbol(keysymbol.clone()),

            super::DefViewItem::Entity(entity) => match entity {
                Entity::Sopheme(sopheme) => DefViewItem::Sopheme(sopheme.clone()),

                _ => DefViewItem::NotImplemented(),
            },

            super::DefViewItem::Rawable(rawable) => match rawable {
                RawableEntity::Entity(entity) => match entity {
                    Entity::Sopheme(sopheme) => DefViewItem::Sopheme(sopheme.clone()),

                    _ => DefViewItem::NotImplemented(),
                },

                _ => DefViewItem::NotImplemented(),
            },
            
            _ => DefViewItem::NotImplemented(),
        }
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
                .skip(1)
                .map(|item| item.index)
                .collect::<Vec<_>>(),
        }
    }
}

#[pymethods]
impl DefViewCursor {
    pub fn tip(&self, py: Python<'_>) -> Result<Option<DefViewItem>, PyErr> {
        self.view.borrow(py).with_rs_result(py, |view_rs| {
            view_rs.read(&self.index_stack)
                .map(|item| item.map(DefViewItem::of))
        })
    }

    pub fn nth(&self, level: usize, py: Python<'_>) -> Result<Option<DefViewItem>, PyErr> {
        dbg!(&self.index_stack[..level], &self.index_stack, level);

        self.view.borrow(py).with_rs_result(py, |view_rs| {
            view_rs.read(&self.index_stack[..level])
                .map(|item| item.map(DefViewItem::of))
        })
    }

    #[getter]
    pub fn stack_len(&self) -> usize {
        self.index_stack.len()
    }
}