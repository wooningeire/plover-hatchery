use std::collections::{HashMap, HashSet};

use pyo3::{prelude::*};

mod entity;
pub use entity::{
    Entity,
    Sopheme,
    Keysymbol,
    Transclusion,
};

// mod iter;
// pub use iter::DefSophemesIter;

pub mod py;


#[derive(Clone)]
pub enum OverridableEntity {
    Entity(Entity),
    Override(Box<Def>),
}

impl OverridableEntity {
    pub fn of(entity: &Entity) -> OverridableEntity {
        OverridableEntity::Entity(entity.clone())
    }
}

#[pyclass]
#[derive(Clone)]
pub struct DefEntities {
    items: Vec<OverridableEntity>,
}

impl DefEntities {
    pub fn new(items: Vec<OverridableEntity>) -> Self {
        DefEntities {
            items,
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Def {
    entities: DefEntities,
    varname: String,
}

impl Def {
    pub fn of(entity_seq: &EntitySeq, varname: String) -> Def {
        Def {
            entities: DefEntities::new(
                entity_seq.entities.iter()
                    .map(|entity| OverridableEntity::of(entity))
                    .collect::<Vec<_>>(),
            ),
            varname,
        }
    }
}

#[pymethods]
impl Def {
    #[new]
    pub fn new(entities: DefEntities, varname: String) -> Def {
        Def {
            entities,
            varname,
        }
    }
}


pub struct DefDict {
    entries: HashMap<String, EntitySeq>,
}

impl DefDict {
    pub fn new() -> Self {
        DefDict {
            entries: HashMap::new(),
        }
    }


    pub fn add(&mut self, varname: String, seq: EntitySeq) {
        self.entries.insert(varname, seq);
    }

    pub fn get_def(&self, varname: &str) -> Option<Def> {
        self.entries.get(varname)
            .map(|entity_seq| Def::of(entity_seq, varname.to_string()))
    }
}


#[pyclass]
#[derive(Clone)]
pub struct EntitySeq {
    #[pyo3(get)] pub entities: Vec<Entity>,
}

#[pymethods]
impl EntitySeq {
    #[new]
    pub fn new(entities: Vec<Entity>) -> Self {
        EntitySeq {
            entities,
        }
    }
}



#[pyclass]
pub struct SophemeSeq {
    items: Vec<Sopheme>,
}

impl SophemeSeq {
    pub fn new(sophemes: Vec<Sopheme>) -> Self {
        SophemeSeq {
            items: sophemes,
        }
    }
}

struct DefView<'a> {
    defs: &'a DefDict,
    base_def: &'a Def,
}


impl<'a> DefView<'a> {
    pub fn new(defs: &'a DefDict, base_def: &'a Def) -> Self {
        DefView {
            defs,
            base_def,
        }
    }

    
    pub fn collect_sophemes(&self) -> Result<SophemeSeq, &'static str> {
        fn dfs(def: &Def, dict: &DefDict, sophemes: &mut Vec<Sopheme>, visited: &mut HashSet<String>) -> Result<(), &'static str> {
            visited.insert(def.varname.clone());

            for overridable_entity in def.entities.items.iter() {
                match overridable_entity {
                    OverridableEntity::Entity(entity) => match entity {
                        Entity::Sopheme(sopheme) => {
                            sophemes.push(sopheme.clone());
                        },

                        Entity::Transclusion(transclusion) => {
                            if visited.contains(&transclusion.target_varname) {
                                return Err("circular dependency");
                            }

                            match dict.get_def(&transclusion.target_varname) {
                                Some(inner_def) => {
                                    dfs(&inner_def, dict, sophemes, visited)?;
                                },
                                None => {
                                    return Err("entry is not defined");
                                },
                            };
                        },
                    },

                    OverridableEntity::Override(child_def) => {
                        dfs(child_def, dict, sophemes, visited)?;
                    },
                }
            }
            
            visited.remove(&def.varname.clone());

            Ok(())
        }


        let mut sophemes: Vec<Sopheme> = Vec::new();
        dfs(&self.base_def, &self.defs, &mut sophemes, &mut HashSet::new())?;

        Ok(SophemeSeq::new(sophemes))
    }

    pub fn translation(&self) -> Result<String, &'static str> {
        self.collect_sophemes()
            .map(
                |sophemes| sophemes.items.iter()
                    .map(|sopheme| sopheme.chars.clone())
                    .collect::<Vec<_>>()
                    .join("")
            )
    }


    // pub fn sophemes(&self) -> DefSophemesIter<'a> {
    //     DefSophemesIter::new(&self.base_def)
    // }
}