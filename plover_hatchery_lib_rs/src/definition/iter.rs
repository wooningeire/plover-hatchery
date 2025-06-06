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

pub struct DefViewCursor<'a> {
    defs: &'a DefDict,
    pub stack: Vec<DefViewItemRefIter<'a>>,
}

impl<'a> DefViewCursor<'a> {
    pub fn of_view<'b>(view: &'b DefView<'a>) -> Self
        where 'b: 'a
    {
        DefViewCursor {
            defs: view.defs,

            stack: vec![DefViewItemRefIter::new(view.root.as_item())],
        }
    }

    pub fn step(&mut self) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        // Step in
        if let Some(val) = self.stack.last()?.create_child_iter(self.defs) {
            match val {
                Ok(iter) => {
                    self.stack.push(iter);
                },

                Err(err) => return Some(Err(err)),
            }
        }

        loop {
            // Step over
            match self.stack.last_mut()?.next(self.defs) {
                Some(item_ref) => {
                    return Some(item_ref);
                },

                None => {
                    // Step out
                    self.stack.pop();
                },
            }
        }
    }
}


#[cfg(test)]
mod test {
    use super::*;


}