use std::sync::Arc;

use pyo3::{prelude::*};

mod entity;
pub use entity::{
    Entity,
    Sopheme,
    Keysymbol,
    Transclusion,
};

#[pyclass]
pub struct Definition {
    entities: Vec<Entity>,
}


pub enum Cursor {
    Definition(DefinitionCursor),
    Sopheme(SophemeCursor),
}


#[pyclass]
pub struct DefinitionCursor {
    definition: Arc<Definition>,
    entity_index: usize,
    inner: Box<Cursor>,
}

#[pyclass]
pub struct SophemeCursor {
    sopheme: Arc<Sopheme>,
    sopheme_index: usize,
    keysymbol_index: usize,
}