use std::collections::{HashMap, HashSet};

use pyo3::{prelude::*};

mod entity;
pub use entity::{
    Entity,
    Sopheme,
    Keysymbol,
    Transclusion,
};

mod iter;
pub use iter::{
    DefViewCursor,
    StepData,
    StackItem,
};

pub mod py;


#[pyclass]
#[derive(Clone)]
pub enum RawableEntity {
    Entity(Entity),
    RawDef(Def),
}

impl RawableEntity {
    pub fn get<'a>(&'a self, index: usize, defs: &'a DefDict) -> Result<Option<DefViewItem<'a>>, &'static str> {
        match self {
            RawableEntity::Entity(entity) => Ok(entity.get(index, defs)?),

            RawableEntity::RawDef(def) => Ok(def.get(index)),
        }
    }
}

#[derive(Clone)]
pub struct OverridableEntitySeq {
    items: Vec<RawableEntity>,
}

impl OverridableEntitySeq {
    pub fn new(items: Vec<RawableEntity>) -> Self {
        OverridableEntitySeq {
            items,
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Def {
    entities: OverridableEntitySeq,
    varname: String,
}

impl Def {
    pub fn of(entity_seq: EntitySeq, varname: String) -> Def {
        Def {
            entities: OverridableEntitySeq::new(
                entity_seq.entities.into_iter()
                    .map(|entity| RawableEntity::Entity(entity))
                    .collect::<Vec<_>>(),
            ),
            varname,
        }
    }

    pub fn get<'a>(&'a self, index: usize) -> Option<DefViewItem<'a>> {
        self.entities.items.get(index)
            .map(DefViewItem::Rawable)
    }
}

impl Def {
    pub fn new(entities: OverridableEntitySeq, varname: String) -> Def {
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

impl SophemeSeq {
    pub fn new(sophemes: Vec<Sopheme>) -> Self {
        SophemeSeq {
            items: sophemes,
        }
    }
}


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

    fn as_item(&'a self) -> DefViewItem<'a> {
        DefViewItem::Root(&self.def_ref())
    }
}

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

            for overridable_entity in def.entities.items.iter() {
                dfs(overridable_entity, dict, sophemes, visited);
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


    pub fn read(&'a self, cursor: &Vec<usize>) -> Result<Option<DefViewItem<'a>>, &'static str> {
        let mut cur_entity = self.root.as_item();

        for index in cursor {
            match cur_entity {
                DefViewItem::Root(def) => match def.get(index) {
                    Some(item) => {
                        cur_entity = item;
                    },

                    None => return Ok(None),
                },

                DefViewItem::Rawable(rawable) => match rawable.get(index, self.defs)? {
                    Some(item) => {
                        cur_entity = item;
                    },

                    None => return Ok(None),
                },

                DefViewItem::Entity(entity) => match entity.get(index, self.defs)? {
                    Some(item) => {
                        cur_entity = item;
                    },

                    None => return Ok(None),
                },

                DefViewItem::Keysymbol(_) => return Ok(None),
            }
        }

        Ok(Some(cur_entity))
    }
}


#[derive(Clone)]
pub enum DefViewItem<'a> {
    Root(&'a Def),
    Rawable(&'a RawableEntity),
    Entity(&'a Entity),
    Keysymbol(&'a Keysymbol),
}

impl<'a> DefViewItem<'a> {
    pub fn get(&self, index: usize, defs: &'a DefDict) -> Result<Option<DefViewItem<'a>>, &'static str> {
        match self {
            DefViewItem::Root(def) => Ok(def.get(index)),

            DefViewItem::Rawable(rawable) => Ok(rawable.get(0, defs)?),

            DefViewItem::Entity(entity) => Ok(entity.get(0, defs)?),

            _ => Ok(None),
        }
    }

    pub fn get_if_sopheme(&self) -> Option<&'a Sopheme> {
        match self {
            DefViewItem::Rawable(rawable) => match rawable {
                RawableEntity::Entity(entity) => entity.get_if_sopheme(),

                _ => None,
            },

            DefViewItem::Entity(entity) => entity.get_if_sopheme(),

            _ => None,
        }
    }
}