use super::*;

pub struct DefViewItemRefIter<'a> {
    item_ref: DefViewItemRef<'a>,
    index: Option<usize>,
}

impl<'a> DefViewItemRefIter<'a> {
    pub fn new(item_ref: DefViewItemRef<'a>) -> Self {
        DefViewItemRefIter {
            item_ref,
            index: None,
        }
    }

    pub fn create_child_iter(&self, defs: &'a DefDict) -> Option<Result<Self, &'static str>> {
        Some(
            self.item_ref.get(self.index?, defs)?
                .map(DefViewItemRefIter::new)
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
}