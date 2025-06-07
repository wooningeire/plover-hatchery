use super::*;

pub struct DefViewItemRefChildrenCursor<'a> {
    item_ref: DefViewItemRef<'a>,
    index: Option<usize>,
}

impl<'a> DefViewItemRefChildrenCursor<'a> {
    pub fn new(item_ref: DefViewItemRef<'a>) -> Self {
        DefViewItemRefChildrenCursor {
            item_ref,
            index: None,
        }
    }

    pub fn create_child_iter(&self, defs: &'a DefDict) -> Option<Result<Self, &'static str>> {
        Some(
            self.item_ref.get(self.index?, defs)?
                .map(DefViewItemRefChildrenCursor::new)
        )
    }

    fn peek(&self, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        self.item_ref.get(self.index?, defs)
    }

    pub fn next(&mut self, defs: &'a DefDict) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        self.incr();
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