use super::*;

pub struct DefViewItemRefChildrenCursor<'a> {
    item_ref: DefViewItemRef<'a>,
    index: Option<usize>,
}

impl<'a> DefViewItemRefChildrenCursor<'a> {
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

    pub fn create_child_iter_at_start(&self, defs: &'a DefDict) -> Option<Result<Self, &'static str>> {
        Some(
            self.item_ref.get_child(self.index?, defs)?
                .map(DefViewItemRefChildrenCursor::new_at_start)
        )
    }

    pub fn create_child_iter_at_end(&self, defs: &'a DefDict) -> Option<Result<Self, &'static str>> {
        Some(
            self.item_ref.get_child(self.index?, defs)?
                .map(DefViewItemRefChildrenCursor::new_at_end)
        )
    }

    pub fn peek(&self, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        self.item_ref.get_child(self.index?, defs)
    }

    pub fn next(&mut self, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        self.incr();
        self.peek(defs)
    }

    pub fn prev(&mut self, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
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


    pub fn iter_mut<'cur>(&'cur mut self, defs: &'a DefDict) -> DefViewItemRefChildrenIter<'a, 'cur> {
        DefViewItemRefChildrenIter {
            cursor: self,
            defs,
        }
    }
}

pub struct DefViewItemRefChildrenIter<'defs, 'cur> {
    cursor: &'cur mut DefViewItemRefChildrenCursor<'defs>,
    defs: &'defs DefDict,
}

impl<'defs, 'cur> Iterator for DefViewItemRefChildrenIter<'defs, 'cur> {
    type Item = Result<DefViewItemRef<'defs>, &'static str>;

    fn next(&mut self) -> Option<Self::Item> {
        self.cursor.next(self.defs)
    }
}