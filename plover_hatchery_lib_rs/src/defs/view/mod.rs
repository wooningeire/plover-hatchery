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

use pyo3::{exceptions::PyException, PyErr};

pub mod py;


#[derive(Clone, Debug)]

pub enum DefViewRoot<'a> {
    Def(Def),
    DefRef(&'a Def),
}

impl<'a> DefViewRoot<'a> {
    pub fn def_ref(&self) -> &Def {
        match self {
            DefViewRoot::Def(ref def) => def,

            DefViewRoot::DefRef(def) => def,
        }
    }

    pub fn as_item_ref(&self) -> DefViewItemRef {
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

    pub fn get_entry(defs: &'a DefDict, varname: &str) -> Result<DefView<'a>, DefViewErr> {
        Ok(
            DefView::new(
                defs,
                defs.get_def(varname).ok_or(DefViewErr::MissingEntry { varname: varname.to_string() })?)
        )
    }
    
    pub fn collect_sophemes(&self) -> Result<SophemeSeq, DefViewErr> {
        fn dfs(entity: &RawableEntity, dict: &DefDict, sophemes: &mut Vec<Sopheme>, visited: &mut HashSet<String>) -> Result<(), DefViewErr> {
            match entity {
                RawableEntity::Entity(entity) => match entity {
                    Entity::Sopheme(sopheme) => {
                        sophemes.push(sopheme.clone());
                    },

                    Entity::Transclusion(transclusion) => {
                        if visited.contains(&transclusion.target_varname) {
                            return Err(DefViewErr::UnexpectedNone);
                        }

                        match dict.get_def(&transclusion.target_varname) {
                            Some(inner_def) => {
                                dfs_def(&inner_def, dict, sophemes, visited)?;
                            },
                            None => return Err(DefViewErr::MissingEntry { varname: transclusion.target_varname.clone() }),
                        };
                    },
                },

                RawableEntity::RawDef(child_def) => {
                    dfs_def(child_def, dict, sophemes, visited)?;
                },
            }

            Ok(())
        }


        fn dfs_def(def: &Def, dict: &DefDict, sophemes: &mut Vec<Sopheme>, visited: &mut HashSet<String>) -> Result<(), DefViewErr> {
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

    pub fn translation(&self) -> Result<String, DefViewErr> {
        self.collect_sophemes()
            .map(
                |sophemes| sophemes.items.iter()
                    .map(|sopheme| sopheme.chars.clone())
                    .collect::<Vec<_>>()
                    .join("")
            )
    }


    pub fn get(&self, indexes: &[usize]) -> Result<Option<DefViewItemRef>, DefViewErr> {
        let mut cur_item_ref = self.root.as_item_ref();

        for &index in indexes {
            cur_item_ref = match cur_item_ref.get_child(index, self.defs)? {
                Some(item_ref) => item_ref,

                None => return Ok(None),
            };
        }

        Ok(Some(cur_item_ref))
    }

    pub fn foreach(&self, func: impl Fn(DefViewItemRef, &DefViewCursor)) -> Result<(), DefViewErr> {
        let mut cursor = DefViewCursor::of_view_at_start(self);

        while let Some(item_ref) = cursor.step_forward()? {
            func(item_ref, &cursor);
        }

        Ok(())
    }

    pub fn first_index_after(&self, mut cursor: DefViewCursor<'a, '_>, predicate: impl Fn(DefViewItemRef) -> bool) -> Result<Option<DefViewCursor<'a, '_>>, DefViewErr> {
        while let Some(item_ref) = cursor.step_forward()? {
            if predicate(item_ref) {
                return Ok(Some(cursor));
            }
        }

        Ok(None)
    }

    pub fn last_index_before(&self, mut cursor: DefViewCursor<'a, '_>, predicate: impl Fn(DefViewItemRef) -> bool) -> Result<Option<DefViewCursor<'a, '_>>, DefViewErr> {
        while let Some(item_ref) = cursor.step_backward()? {
            if predicate(item_ref) {
                return Ok(Some(cursor));
            }
        }

        Ok(None)
    }

    pub fn first_index_since(&self, cursor: DefViewCursor<'a, '_>, predicate: impl Fn(DefViewItemRef) -> bool) -> Result<Option<DefViewCursor<'a, '_>>, DefViewErr> {
        if let Some(item_ref) = cursor.peek()? {
            if predicate(item_ref) {
                return Ok(Some(cursor));
            }
        }

        self.first_index_after(cursor, predicate)
    }
    
    pub fn last_index_until(&self, cursor: DefViewCursor<'a, '_>, predicate: impl Fn(DefViewItemRef) -> bool) -> Result<Option<DefViewCursor<'a, '_>>, DefViewErr> {
        if let Some(item_ref) = cursor.peek()? {
            if predicate(item_ref) {
                return Ok(Some(cursor));
            }
        }

        self.last_index_before(cursor, predicate)
    }


    pub fn first_index(&self, predicate: impl Fn(DefViewItemRef) -> bool) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.first_index_since(DefViewCursor::of_view_at_start(self), predicate)
    }

    pub fn last_index(&self, predicate: impl Fn(DefViewItemRef) -> bool) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.last_index_until(DefViewCursor::of_view_at_end(self)?, predicate)
    }

    pub fn first_keysymbol_cur(&self, predicate: impl Fn(&Keysymbol) -> bool) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.first_index(|item_ref| match item_ref {
            DefViewItemRef::Keysymbol(keysymbol) => predicate(keysymbol),

            _ => false,
        })
    }

    pub fn last_keysymbol_cur(&self, predicate: impl Fn(&Keysymbol) -> bool) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.last_index(|item_ref| match item_ref {
            DefViewItemRef::Keysymbol(keysymbol) => predicate(keysymbol),

            _ => false,
        })
    }

    pub fn first_consonant_cur(&self) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.first_keysymbol_cur(|keysymbol| keysymbol.is_consonant())
    }

    pub fn last_consonant_cur(&self) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.last_keysymbol_cur(|keysymbol| keysymbol.is_consonant())
    }

    pub fn first_vowel_cur(&self) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.first_keysymbol_cur(|keysymbol| keysymbol.is_vowel())
    }

    pub fn last_vowel_cur(&self) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.last_keysymbol_cur(|keysymbol| keysymbol.is_vowel())
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
    pub fn get_child(&self, index: usize, defs: &'a DefDict) -> Result<Option<DefViewItemRef<'a>>, DefViewErr> {
        Ok(match self {
            DefViewItemRef::Sopheme(sopheme) => match sopheme.get_child(index) {
                Some(keysymbol) => Some(DefViewItemRef::Keysymbol(keysymbol)),

                None => None,
            },

            DefViewItemRef::Def(def) => match def.get_child(index) {
                Some(rawable) => match rawable {
                    RawableEntity::Entity(entity) => match entity {
                        Entity::Sopheme(sopheme) => Some(DefViewItemRef::Sopheme(sopheme)),

                        Entity::Transclusion(transclusion) => match defs.get(&transclusion.target_varname) {
                            Some(seq) => Some(DefViewItemRef::EntitySeq(seq, transclusion.target_varname.clone())),

                            None => return Err(DefViewErr::MissingEntry { varname: transclusion.target_varname.clone() }),
                        },
                    },

                    RawableEntity::RawDef(def) => Some(DefViewItemRef::Def(def)),
                },

                None => None,
            },

            DefViewItemRef::EntitySeq(seq, _) => match seq.entities.get(index) {
                Some(entity) => match entity {
                    Entity::Sopheme(sopheme) => Some(DefViewItemRef::Sopheme(sopheme)),

                    Entity::Transclusion(transclusion) => match defs.get(&transclusion.target_varname) {
                        Some(seq) => Some(DefViewItemRef::EntitySeq(seq, transclusion.target_varname.clone())),

                        None => return Err(DefViewErr::MissingEntry { varname: transclusion.target_varname.clone() }),
                    },
                },

                None => None,
            },

            _ => None,
        })
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


pub struct DefViewItemRefModified<'a> {
    item_ref: DefViewItemRef<'a>,
    stress_modifier: u8,
}

impl<'a> DefViewItemRefModified<'a> {
    pub fn new(item_ref: DefViewItemRef<'a>, stress_modifier: u8) -> DefViewItemRefModified<'a> {
        DefViewItemRefModified {
            item_ref,
            stress_modifier,
        }
    }
}


pub enum DefViewErr {
    MissingEntry {
        varname: String,
    },
    EmptyStack,
    UnexpectedNone,
    CircularDependency {
        def_varname: String,
        varname: String,
    },
    UnexpectedChildItemType,
}

impl DefViewErr {
    pub fn message(&self) -> String {
        match self {
            DefViewErr::MissingEntry { varname } =>
                format!("There is no entry for \"{varname}\""),

            DefViewErr::EmptyStack =>
                format!("Cursor stack is empty"),

            DefViewErr::UnexpectedNone =>
                format!("Expected this cursor to be pointing to an item"),

            DefViewErr::CircularDependency { def_varname, varname } => 
                format!("Definition for \"{def_varname}\" contains a circular dependency \"{varname}\""),

            DefViewErr::UnexpectedChildItemType =>
                format!("Unexpected child item type"),
        }
    }

    pub fn as_pyerr(&self) -> PyErr {
        PyException::new_err(self.message())
    }
}