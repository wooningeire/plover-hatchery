use super::*;

mod iter;
pub use iter::{
    DefViewItemRefChildrenCursor,
    DefViewItemRefChildrenIter,
};

pub mod py;

#[derive(Clone)]
pub struct DefViewCursor<'defs, 'view>
    where 'view: 'defs
{
    pub view: &'view DefView<'defs>,
    pub stack: Vec<DefViewItemRefChildrenCursor<'defs>>,
}

impl<'defs, 'view> DefViewCursor<'defs, 'view> {
    pub fn of_view_at_start(view: &'view DefView<'defs>) -> Self {
        DefViewCursor {
            view,

            stack: vec![DefViewItemRefChildrenCursor::new_at_start(view.root().as_item_ref())],
        }
    }

    pub fn of_view_at_end(view: &'view DefView<'defs>) -> Self {
        let mut cursor = DefViewCursor {
            view,

            stack: vec![DefViewItemRefChildrenCursor::new_at_end(view.root().as_item_ref())],
        };

        cursor.drill_in();

        cursor
    }

    pub fn with_index_stack(view: &'view DefView<'defs>, mut indexes: impl Iterator<Item = Option<usize>>) -> Result<Self, &'static str> {
        let mut cursor = DefViewCursor {
            view,

            stack: match indexes.next() {
                Some(first_index) => vec![DefViewItemRefChildrenCursor::new(view.root().as_item_ref(), first_index)],

                None => vec![],
            },
        };

        for index in indexes {
            cursor.step_in_at(index)?;
        }

        Ok(cursor)
    }

    pub fn peek(&self) -> Result<Option<DefViewItemRef<'defs>>, &'static str> {
        if let Some(iter) = self.stack.last() {
            return iter.peek(self.view.defs());
        }

        Ok(Some(self.view.root().as_item_ref()))
    }

    pub fn step_forward(&mut self) -> Result<Option<DefViewItemRef<'defs>>, &'static str> {
        match self.step_in_at_start() {
            Some(Err(msg)) => return Err(msg),

            _ => {},
        }
        
        self.step_over_forward()
    }

    pub fn step_backward(&mut self) -> Result<Option<DefViewItemRef<'defs>>, &'static str> {
        self.step_over_backward()
    }

    pub fn step_in_at_start(&mut self) -> Option<Result<(), &'static str>> {
        match self.stack.last()?.create_child_iter_at_start(self.view.defs())? {
            Ok(iter) => {
                self.stack.push(iter);
            },

            Err(err) => return Some(Err(err)),
        }

        Some(Ok(()))
    }

    pub fn step_in_at_end(&mut self) -> Option<Result<(), &'static str>> {
        match self.stack.last()?.create_child_iter_at_end(self.view.defs())? {
            Ok(iter) => {
                self.stack.push(iter);
            },

            Err(err) => return Some(Err(err)),
        }

        Some(Ok(()))
    }

    pub fn step_in_at(&mut self, index: Option<usize>) -> Result<(), &'static str> {
        match self.stack.last() {
            Some(iter) => match iter.create_child_iter_at(self.view.defs(), index)? {
                Some(iter) => {
                    self.stack.push(iter);
                },

                None => return Err("no child at this index"),
            },

            None => return Err("stack is empty"),
        }

        Ok(())
    }

    pub fn step_over_forward(&mut self) -> Result<Option<DefViewItemRef<'defs>>, &'static str> {
        loop {
            match self.stack.last_mut() {
                Some(iter) => match iter.next(self.view.defs())? {
                    Some(item_ref) => {
                        return Ok(Some(item_ref));
                    },

                    None => {
                        self.step_out();
                    },
                },

                None => return Ok(None),
            }
        }
    }

    pub fn step_over_backward(&mut self) -> Result<Option<DefViewItemRef<'defs>>, &'static str> {
        // TODO make this more consistent with forward
        match self.stack.last_mut() {
            Some(iter) => match iter.prev(self.view.defs())? {
                Some(_) => {
                    self.drill_in();
                },

                None => {
                    self.step_out();
                },
            }

            None => return Ok(None),
        }

        match self.stack.last() {
            Some(iter) => Ok(iter.peek(self.view.defs())?),

            None => Ok(None)
        }
    }

    fn drill_in(&mut self) {
        while let Some(_) = self.step_in_at_end() {}
        self.stack.pop(); // last index will be a None
    }

    pub fn step_out(&mut self) {
        self.stack.pop();
    }

    pub fn index_stack(&self) -> Vec<usize> {
        self.stack.iter()
            .map(|iter| iter.index() )
            .take_while(|iter| iter.is_some())
            .map(|index| index.unwrap())
            .collect::<Vec<_>>()
    }
}


// #[cfg(test)]
// mod test {
//     use super::*;


// }