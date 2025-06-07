use std::collections::HashSet;

use super::{
    def_items::{
        Keysymbol,
        Entity,
        Sopheme,
        SophemeSeq,
        RawableEntity,
    },
    def::Def,
    dict::DefDict,
    cursor::DefViewCursor,
};

pub mod py;


#[derive(Clone, Debug)]

pub enum DefViewRoot<'a> {
    Def(Def),
    DefRef(&'a Def),
}

impl<'a> DefViewRoot<'a> {
    pub fn def_ref(&'a self) -> &'a Def {
        match self {
            DefViewRoot::Def(ref def) => def,

            DefViewRoot::DefRef(def) => def,
        }
    }

    pub fn as_item(&'a self) -> DefViewItemRef<'a> {
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

    pub fn defs(&self) -> &'a DefDict {
        self.defs
    }

    pub fn root(&self) -> &DefViewRoot<'a> {
        &self.root
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

            for overridable_entity in def.rawables.iter() {
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

    pub fn foreach(&self, func: impl Fn(DefViewItemRef, &DefViewCursor)) -> Result<(), &'static str> {
        let mut cursor = DefViewCursor::of_view(self);

        while let Some(item_ref) = cursor.step() {
            func(item_ref?, &cursor);
        }

        Ok(())
    }
}


// fn map_sopheme(sopheme: &Sopheme, cursor: &mut DefViewCursor, func: impl Fn(DefViewItemRef, &DefViewCursor)) -> Result<Def, &'static str> {
//     let mut new_def = Sopheme::empty(sopheme.chars);
//     let level = cursor.stack.len();

//     while let Some(item_ref) = cursor.step() {
//         if cursor.stack.len() < level {
//             break;
//         }

//         func(item_ref?, &cursor);
//     }

//     Ok(new_def)
// }


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