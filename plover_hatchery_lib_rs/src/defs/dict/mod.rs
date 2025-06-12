use std::collections::HashMap;

use super::{
    def_items::{
        Def,
        Entity,
    },
};

pub mod py;

pub struct DefDict {
    pub entries: HashMap<String, Vec<Entity>>,
}

impl DefDict {
    pub fn new() -> Self {
        DefDict {
            entries: HashMap::new(),
        }
    }


    pub fn add(&mut self, varname: String, entities: Vec<Entity>) {
        self.entries.insert(varname, entities);
    }

    pub fn get_def(&self, varname: &str) -> Option<Def> {
        self.entries.get(varname)
            .map(|entity_seq| Def::of(entity_seq.clone(), varname.to_string()))
    }

    pub fn get<'a>(&'a self, varname: &str) -> Option<&'a Vec<Entity>> {
        self.entries.get(varname)
    }
}
