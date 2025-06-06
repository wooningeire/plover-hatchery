use std::collections::{HashMap, HashSet};

use pyo3::{prelude::*};

mod entity;
pub use entity::{
    Entity,
    Sopheme,
    Keysymbol,
    Transclusion,
};

mod cursor;
pub use cursor::{
    DefViewCursor,
};

pub mod py;


#[pyclass]
#[derive(Clone, Debug)]
pub enum RawableEntity {
    Entity(Entity),
    RawDef(Def),
}

impl RawableEntity {
    pub fn get<'a>(&'a self, index: usize, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        match self {
            RawableEntity::Entity(entity) => entity.get(index, defs),

            RawableEntity::RawDef(def) => def.get(index).map(Ok),
        }
    }
}

#[pymethods]
impl RawableEntity {
    pub fn maybe_entity(&self) -> Option<Entity> {
        match self {
            RawableEntity::Entity(entity) => Some(entity.clone()),

            _ => None,
        }
    }

    pub fn maybe_raw_def(&self) -> Option<Def> {
        match self {
            RawableEntity::RawDef(def) => Some(def.clone()),

            _ => None,
        }
    }
}

#[derive(Clone, Debug)]
pub struct RawableSeq {
    rawables: Vec<RawableEntity>,
}

impl RawableSeq {
    pub fn new(rawables: Vec<RawableEntity>) -> Self {
        RawableSeq {
            rawables,
        }
    }
}

#[pyclass]
#[derive(Clone, Debug)]
pub struct Def {
    rawable_seq: RawableSeq,
    #[pyo3(get)] varname: String,
}

impl Def {
    pub fn of(entity_seq: EntitySeq, varname: String) -> Def {
        Def {
            rawable_seq: RawableSeq::new(
                entity_seq.entities.into_iter()
                    .map(|entity| RawableEntity::Entity(entity))
                    .collect::<Vec<_>>(),
            ),
            varname,
        }
    }

    pub fn get<'a>(&'a self, index: usize) -> Option<DefViewItemRef<'a>> {
        self.rawable_seq.rawables.get(index)
            .map(DefViewItemRef::Rawable)
    }

    pub fn new(rawable_seq: RawableSeq, varname: String) -> Def {
        Def {
            rawable_seq,
            varname,
        }
    }

    pub fn empty(varname: String) -> Def {
        Def {
            rawable_seq: RawableSeq::new(vec![]),
            varname,
        }
    }
}

#[pymethods]
impl Def {
    #[getter]
    pub fn rawables(&self) -> Vec<RawableEntity> {
        self.rawable_seq.rawables.clone()
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
            .map(|entity_seq| Def::of(entity_seq.clone(), varname.to_string()))
    }

    pub fn get<'a>(&'a self, varname: &str) -> Option<&'a EntitySeq> {
        self.entries.get(varname)
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

#[pymethods]
impl SophemeSeq {
    #[new]
    pub fn new(sophemes: Vec<Sopheme>) -> Self {
        SophemeSeq {
            items: sophemes,
        }
    }
}

#[derive(Clone, Debug)]

enum DefViewRoot<'a> {
    Def(Def),
    DefRef(&'a Def),
}

impl<'a> DefViewRoot<'a> {
    fn def_ref(&'a self) -> &'a Def {
        match self {
            DefViewRoot::Def(ref def) => def,

            DefViewRoot::DefRef(def) => def,
        }
    }

    fn as_item(&'a self) -> DefViewItemRef<'a> {
        DefViewItemRef::Root(&self.def_ref())
    }
}

#[derive(Clone)]
pub struct DefView<'a> {
    defs: &'a DefDict,
    root: DefViewRoot<'a>,
}


impl<'a> DefView<'a> {
    pub fn new(defs: &'a DefDict, root_def: Def) -> Self {
        DefView {
            defs,
            root: DefViewRoot::Def(root_def),
        }
    }

    pub fn new_ref(defs: &'a DefDict, root_def: &'a Def) -> Self {
        DefView {
            defs,
            root: DefViewRoot::DefRef(root_def),
        }
    }

    pub fn get_entry(defs: &'a DefDict, varname: &str) -> Result<DefView<'a>, &'static str> {
        Ok(
            DefView::new(defs, defs.get_def(varname).ok_or("entry is not defined")?)
        )
    }
    
    pub fn collect_sophemes(&self) -> Result<SophemeSeq, &'static str> {
        fn dfs(entity: &RawableEntity, dict: &DefDict, sophemes: &mut Vec<Sopheme>, visited: &mut HashSet<String>) -> Result<(), &'static str> {
            match entity {
                RawableEntity::Entity(entity) => match entity {
                    Entity::Sopheme(sopheme) => {
                        sophemes.push(sopheme.clone());
                    },

                    Entity::Transclusion(transclusion) => {
                        if visited.contains(&transclusion.target_varname) {
                            return Err("circular dependency");
                        }

                        match dict.get_def(&transclusion.target_varname) {
                            Some(inner_def) => {
                                dfs_def(&inner_def, dict, sophemes, visited)?;
                            },
                            None => {
                                return Err("entry is not defined");
                            },
                        };
                    },
                },

                RawableEntity::RawDef(child_def) => {
                    dfs_def(child_def, dict, sophemes, visited)?;
                },
            }

            Ok(())
        }


        fn dfs_def(def: &Def, dict: &DefDict, sophemes: &mut Vec<Sopheme>, visited: &mut HashSet<String>) -> Result<(), &'static str> {
            visited.insert(def.varname.clone());

            for overridable_entity in def.rawable_seq.rawables.iter() {
                dfs(overridable_entity, dict, sophemes, visited)?;
            }
            
            visited.remove(&def.varname.clone());

            Ok(())
        }


        let mut sophemes: Vec<Sopheme> = Vec::new();
        
        dfs_def(self.root.def_ref(), &self.defs, &mut sophemes, &mut HashSet::new())?;

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


    pub fn read(&'a self, cursor: &[usize]) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        let mut cur_entity = self.root.as_item();

        for &index in cursor {
            match cur_entity {
                DefViewItemRef::Root(def) => {
                    cur_entity = def.get(index)?;
                },

                DefViewItemRef::Rawable(rawable) => match rawable.get(index, self.defs)? {
                    Ok(item_ref) => {
                        cur_entity = item_ref;
                    },

                    Err(err) => return Some(Err(err)),
                },


                DefViewItemRef::Entity(entity) => match entity.get(index, self.defs)? {
                    Ok(item_ref) => {
                        cur_entity = item_ref;
                    },

                    Err(err) => return Some(Err(err)),
                },

                DefViewItemRef::Keysymbol(_) => return None,
            }
        }

        Some(Ok(cur_entity))
    }
}


#[derive(Clone, Debug)]
pub enum DefViewItemRef<'a> {
    Root(&'a Def),
    Rawable(&'a RawableEntity),
    Entity(&'a Entity),
    Keysymbol(&'a Keysymbol),
}

impl<'a> DefViewItemRef<'a> {
    pub fn get(&self, index: usize, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        match self {
            DefViewItemRef::Root(def) => def.get(index).map(Ok),

            DefViewItemRef::Rawable(rawable) => rawable.get(index, defs),

            DefViewItemRef::Entity(entity) => entity.get(index, defs),

            _ => None,
        }
    }

    pub fn get_if_sopheme(&self) -> Option<&'a Sopheme> {
        match self {
            DefViewItemRef::Rawable(rawable) => match rawable {
                RawableEntity::Entity(entity) => entity.get_if_sopheme(),

                _ => None,
            },

            DefViewItemRef::Entity(entity) => entity.get_if_sopheme(),

            _ => None,
        }
    }
}