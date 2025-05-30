use std::{collections::{HashMap, HashSet}, env::VarsOs, sync::Arc};

use pyo3::{exceptions::PyException, prelude::*};

mod entity;
pub use entity::{
    Entity,
    Sopheme,
    Keysymbol,
    Transclusion,
};


#[pyclass]
pub struct DefinitionDictionary {
    entries: HashMap<String, Definition>,
}

#[pymethods]
impl DefinitionDictionary {
    #[new]
    pub fn new() -> Self {
        DefinitionDictionary {
            entries: HashMap::new(),
        }
    }

    pub fn sophemes_in(&self, definition: &Definition, varname: &str) -> Result<Vec<Sopheme>, PyErr> {
        fn dfs(def: &Definition, varname: &str, dict: &DefinitionDictionary, sophemes: &mut Vec<Sopheme>, visited: &mut HashSet<String>) -> Result<(), &'static str> {
            visited.insert(varname.to_string());

            for entity in def.entities.iter() {
                match entity {
                    Entity::Sopheme(sopheme) => sophemes.push(sopheme.clone()),
                    Entity::Transclusion(transclusion) => {
                        if visited.contains(&transclusion.target_varname) {
                            return Err("circular dependency");
                        }

                        match dict.entries.get(&transclusion.target_varname) {
                            Some(inner_def) => {
                                dfs(inner_def, &transclusion.target_varname, dict, sophemes, visited)?;
                            },
                            None => {
                                return Err("entry is not defined");
                            },
                        };
                    },
                }
            }
            
            visited.remove(varname);

            Ok(())
        }


        let mut sophemes: Vec<Sopheme> = Vec::new();
        dfs(definition, varname, self, &mut sophemes, &mut HashSet::new()).map_err(|msg| PyErr::new::<PyException, _>(msg))?;
        Ok(sophemes)
    }

    pub fn add(&mut self, varname: String, definition: Definition) {
        self.entries.insert(varname, definition);
    }

    pub fn foreach(&self, py: Python<'_>, callable: PyObject) {
        for (varname, definition) in self.entries.iter() {
            _ = callable.call(py, (varname, definition.clone()), None);
        }
    }
}


#[pyclass]
#[derive(Clone)]
pub struct Definition {
    #[pyo3(get)] pub entities: Vec<Entity>,
}

#[pymethods]
impl Definition {
    #[new]
    pub fn new(entities: Vec<Entity>) -> Self {
        Definition {
            entities,
        }
    }

    // pub fn loc_first_keysymbol() {

    // }
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
    keysymbol_index: usize,
}