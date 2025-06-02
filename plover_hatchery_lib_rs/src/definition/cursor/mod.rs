use super::*;

pub enum CursorItem<'a> {
    Entity(&'a OverridableEntity),
    Keysymbol(&'a Keysymbol),
}


#[derive(Clone)]
pub enum Cursor<'a> {
    Def(DefCursor<'a>),
    DefRef(DefRefCursor<'a>),
    Sopheme(SophemeCursor<'a>),
}

impl<'a> Cursor<'a> {
    pub fn initial(overridable_entity: &'a OverridableEntity, defs: &DefDict) -> Result<Cursor<'a>, &'static str> {
        match overridable_entity {
            OverridableEntity::Entity(entity) => match entity {
                Entity::Sopheme(sopheme) => Ok(Cursor::Sopheme(SophemeCursor::initial(sopheme))),

                Entity::Transclusion(transclusion) => match defs.get_def(&transclusion.target_varname) {
                    Some(def) => Ok(Cursor::Def(DefCursor::initial(def))),

                    None => Err("could not find transcluded value"),
                },
            },

            OverridableEntity::Override(def) => Ok(Cursor::DefRef(DefRefCursor::initial(def))),
        }
    }

    pub fn cur_tip_item(&'a self) -> Option<CursorItem<'a>> {
        let mut current_cursor: &Cursor<'a> = self;

        while let Some(inner) = current_cursor.get_inner() {
            current_cursor = &inner;
        }

        current_cursor.get_item()
    }

    pub fn get_item(&'a self) -> Option<CursorItem<'a>> {
        match self {
            Cursor::Def(cursor) => cursor.cur_entity().map(CursorItem::Entity),
            Cursor::DefRef(cursor) => cursor.cur_entity().map(CursorItem::Entity),
            Cursor::Sopheme(cursor) => cursor.cur_keysymbol().map(CursorItem::Keysymbol),
        }
    }

    pub fn get_inner(&'a self) -> Option<&'a Box<Cursor<'a>>> {
        match self {
            Cursor::Def(cursor) => cursor.inner.as_ref(),
            Cursor::DefRef(cursor) => cursor.inner.as_ref(),
            Cursor::Sopheme(_) => None,
        }
    }
}

trait CursorOverDefEntities {
    fn initial(def: Def) -> Self;
    fn cur_entity(&self) -> Option<&OverridableEntity>;

}


/// Cursor over entities in an owned definition
#[derive(Clone)]
pub struct DefCursor<'a> {
    def: Def,
    entity_index: usize,
    inner: Option<Box<Cursor<'a>>>,
}

impl<'a> CursorOverDefEntities for DefCursor<'a> {
    fn initial(def: Def) -> DefCursor<'a> {
        DefCursor {
            def,
            entity_index: 0,
            inner: None,
        }
    }

    fn cur_entity(&self) -> Option<&OverridableEntity> {
        self.def.entities.items.get(self.entity_index)
    }
}



/// Cursor over entities in a reference to a definition
#[derive(Clone)]
pub struct DefRefCursor<'a> {
    def: &'a Def,
    entity_index: usize,
    inner: Option<Box<Cursor<'a>>>,
}


impl<'a> DefRefCursor<'a> {
    pub fn initial(def: &'a Def) -> DefRefCursor<'a> {
        DefRefCursor {
            def,
            entity_index: 0,
            inner: None,
        }
    }

    pub fn cur_entity(&self) -> Option<&'a OverridableEntity> {
        self.def.entities.items.get(self.entity_index)
    }

    pub fn step_in(&'a mut self, defs: &DefDict) -> Result<(), &'static str> {
        if self.inner.is_some() {
            return Err("already has an inner cursor");
        }

        let cursor = match self.cur_entity() {
            Some(item) => Cursor::initial(item, defs)?,

            None => return Err("not pointing to an entity"),
        };

        self.inner = Some(Box::new(cursor));

        Ok(())
    }
}

#[derive(Clone)]
pub struct SophemeCursor<'a> {
    sopheme: &'a Sopheme,
    keysymbol_index: usize,
}

impl<'a> SophemeCursor<'a> {
    pub fn initial(sopheme: &'a Sopheme) -> SophemeCursor<'a> {
        SophemeCursor {
            sopheme,
            keysymbol_index: 0,
        }
    }

    pub fn cur_keysymbol(&self) -> Option<&Keysymbol> {
        self.sopheme.keysymbols.get(self.keysymbol_index)
    }

    pub fn next(&mut self) -> Result<(), &'static str> {
        match self.cur_keysymbol() {
            Some(_) => {
                self.keysymbol_index += 1;
                Ok(())
            },
            None => Err("already at end"),
        }
    }
}