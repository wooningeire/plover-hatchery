use super::super::{
    view::{
        DefViewItemRef,
        DefViewErr,
    },
    dict::DefDict,
};

#[derive(Clone)]
pub struct DefViewItemRefChildrenCursor<'a> {
    item_ref: DefViewItemRef<'a>,
    index: Option<usize>,
}

impl<'a> DefViewItemRefChildrenCursor<'a> {
    pub fn new(item_ref: DefViewItemRef<'a>, index: Option<usize>) -> Self {
        DefViewItemRefChildrenCursor {
            item_ref,
            index,
        }
    }

    pub fn new_at_start(item_ref: DefViewItemRef<'a>) -> Self {
        DefViewItemRefChildrenCursor {
            item_ref,
            index: None,
        }
    }

    pub fn new_at_end(item_ref: DefViewItemRef<'a>) -> Self {
        let item_n_children = item_ref.n_children();
        DefViewItemRefChildrenCursor {
            item_ref,
            index: if item_n_children > 0 { Some(item_n_children - 1) } else { None },
        }
    }

    pub fn create_child_iter_at_start(&self, defs: &'a DefDict) -> Result<Option<Self>, DefViewErr> {
        Ok(match self.index {
            Some(index) => match self.item_ref.get_child(index, defs)? {
                Some(item_ref) => Some(DefViewItemRefChildrenCursor::new_at_start(item_ref)),
                
                None => None,
            },

            None => None,
        })
    }

    pub fn create_child_iter_at_end(&self, defs: &'a DefDict) -> Result<Option<Self>, DefViewErr> {
        Ok(match self.index {
            Some(index) => match self.item_ref.get_child(index, defs)? {
                Some(item_ref) => Some(DefViewItemRefChildrenCursor::new_at_end(item_ref)),

                None => None,
            },

            None => None,
        })
    }

    pub fn create_child_iter_at(&self, defs: &'a DefDict, child_index: Option<usize>) -> Result<Option<Self>, DefViewErr> {
        Ok(match self.index {
            Some(index) => match self.item_ref.get_child(index, defs)? {
                Some(item_ref) => Some(DefViewItemRefChildrenCursor::new(item_ref, child_index)),

                None => None,
            },

            None => None,
        })
    }

    pub fn peek(&self, defs: &'a DefDict) -> Result<Option<DefViewItemRef<'a>>, DefViewErr> {
        match self.index {
            Some(index) => self.item_ref.get_child(index, defs),

            None => Ok(None),
        }
    }

    pub fn next(&mut self, defs: &'a DefDict) -> Result<Option<DefViewItemRef<'a>>, DefViewErr> {
        self.incr();
        self.peek(defs)
    }

    pub fn prev(&mut self, defs: &'a DefDict) -> Result<Option<DefViewItemRef<'a>>, DefViewErr> {
        self.decr();
        self.peek(defs)
    }

    fn incr(&mut self) {
        match self.index {
            Some(val) => {
                self.index = Some(val + 1);
            },

            None => {
                self.index = Some(0);
            },
        }
    }

    fn decr(&mut self) {
        match self.index {
            Some(val) => {
                if val == 0 {
                    self.index = None;
                } else {
                    self.index = Some(val - 1);
                }
            },

            _ => {},
        }
    }

    pub fn index(&self) -> Option<usize> {
        self.index
    }
}
