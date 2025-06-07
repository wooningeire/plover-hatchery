use std::collections::HashMap;

use super::{
    def::Def,
    def_items::EntitySeq,
};

pub mod py;

pub struct DefDict {
    pub entries: HashMap<String, EntitySeq>,
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
