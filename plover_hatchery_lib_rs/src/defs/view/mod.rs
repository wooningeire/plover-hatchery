use std::collections::HashSet;

use super::{
    def_items::{
        Keysymbol,
        Entity,
        EntitySeq,
        Sopheme,
        SophemeSeq,
        RawableEntity,
        Def,
    },
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
        DefViewItemRef::Def(&self.def_ref())
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


    pub fn read(&'a self, indexes: &[usize]) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        let mut cur_item_ref = self.root.as_item();

        for &index in indexes {
            cur_item_ref = match cur_item_ref.get_child(index, self.defs)? {
                Ok(item_ref) => item_ref,

                Err(msg) => return Some(Err(msg)),
            }
        }

        Some(Ok(cur_item_ref))
    }

    pub fn foreach(&self, func: impl Fn(DefViewItemRef, &DefViewCursor)) -> Result<(), &'static str> {
        let mut cursor = DefViewCursor::of_view_at_start(self);

        while let Some(item_ref) = cursor.step_forward() {
            func(item_ref?, &cursor);
        }

        Ok(())
    }

    pub fn first_consonant_loc(&self) -> Result<Option<Vec<usize>>, &'static str> {
        let mut cursor = DefViewCursor::of_view_at_start(self);

        while let Some(item_ref) = cursor.step_forward() {
            match item_ref? {
                DefViewItemRef::Keysymbol(keysymbol) => {
                    if keysymbol.is_consonant() {
                        return Ok(Some(cursor.index_stack()));
                    }
                },
                
                _ => {},
            }
        }

        Ok(None)
    }

    pub fn last_consonant_loc(&self) -> Result<Option<Vec<usize>>, &'static str> {
        let mut cursor = DefViewCursor::of_view_at_start(self);

        let mut last_index_stack = None;

        while let Some(item_ref) = cursor.step_forward() {
            match item_ref? {
                DefViewItemRef::Keysymbol(keysymbol) => {
                    if keysymbol.is_consonant() {
                        last_index_stack = Some(cursor.index_stack());
                    }
                },
                
                _ => {},
            }
        }

        Ok(last_index_stack)
        // let mut cursor = DefViewCursor::of_view_at_end(self);

        // dbg!(cursor.index_stack());

        // while let Some(item_ref) = cursor.step_backward() {
        //     dbg!(cursor.index_stack());

        //     match item_ref? {
        //         DefViewItemRef::Keysymbol(keysymbol) => {
        //             if keysymbol.is_consonant() {
        //                 return Ok(Some(cursor.index_stack()));
        //             }
        //         },
                
        //         _ => {},
        //     }
        // }

        // Ok(None)
    }
}


#[derive(Clone, Debug)]
pub enum DefViewItemRef<'a> {
    Keysymbol(&'a Keysymbol),
    Sopheme(&'a Sopheme),
    Def(&'a Def),
    EntitySeq(&'a EntitySeq, String),
}

impl<'a> DefViewItemRef<'a> {

    pub fn get_child(&self, index: usize, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        Some(Ok(match self {
            DefViewItemRef::Sopheme(sopheme) => DefViewItemRef::Keysymbol(sopheme.get_child(index)?),

            DefViewItemRef::Def(def) => match def.get_child(index)? {
                RawableEntity::Entity(entity) => match entity {
                    Entity::Sopheme(sopheme) => DefViewItemRef::Sopheme(sopheme),

                    Entity::Transclusion(transclusion) => match defs.get(&transclusion.target_varname) {
                        Some(seq) => DefViewItemRef::EntitySeq(seq, transclusion.target_varname.clone()),

                        None => return Some(Err("entry not found")),
                    },
                },

                RawableEntity::RawDef(def) => DefViewItemRef::Def(def),
            },

            DefViewItemRef::EntitySeq(seq, _) => match seq.entities.get(index)? {
                Entity::Sopheme(sopheme) => DefViewItemRef::Sopheme(sopheme),

                Entity::Transclusion(transclusion) => match defs.get(&transclusion.target_varname) {
                    Some(seq) => DefViewItemRef::EntitySeq(seq, transclusion.target_varname.clone()),

                    None => return Some(Err("entry not found")),
                },
            },

            _ => return None,
        }))
    }

    pub fn n_children(&self) -> usize {
        match self {
            DefViewItemRef::Sopheme(sopheme) => sopheme.keysymbols.len(),

            DefViewItemRef::Def(def) => def.rawables.len(),

            DefViewItemRef::EntitySeq(seq, _) => seq.entities.len(),

            _ => 0,
        }
    }
}