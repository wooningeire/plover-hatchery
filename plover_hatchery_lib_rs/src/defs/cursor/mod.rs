use super::*;

mod iter;
pub use iter::{
    DefViewItemRefChildrenCursor,
    DefViewItemRefChildrenIter,
};

pub mod py;


pub struct DefViewCursor<'a> {
    pub defs: &'a DefDict,
    pub stack: Vec<DefViewItemRefChildrenCursor<'a>>,
}

impl<'a> DefViewCursor<'a> {
    pub fn of_view_at_start<'b>(view: &'b DefView<'a>) -> Self
        where 'b: 'a
    {
        DefViewCursor {
            defs: view.defs(),

            stack: vec![DefViewItemRefChildrenCursor::new_at_start(view.root().as_item())],
        }
    }

    // pub fn of_view_at_end<'b>(view: &'b DefView<'a>) -> Self
    //     where 'b: 'a
    // {
    //     let mut cursor = DefViewCursor {
    //         defs: view.defs(),

    //         stack: vec![DefViewItemRefChildrenCursor::new_at_end(view.root().as_item())],
    //     };

    //     while let Some(_) = cursor.step_in_at_end() {}

    //     cursor
    // }

    pub fn step_forward(&mut self) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        if let Some(val) = self.step_in_at_start() {
            if let Err(msg) = val {
                return Some(Err(msg));
            }
        }
        
        self.step_over_forward()
    }

    // pub fn step_backward(&mut self) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
    //     self.step_over_backward()
    // }

    pub fn step_in_at_start(&mut self) -> Option<Result<(), &'static str>> {
        match self.stack.last()?.create_child_iter_at_start(self.defs)? {
            Ok(iter) => {
                self.stack.push(iter);
            },

            Err(err) => return Some(Err(err)),
        }

        Some(Ok(()))
    }

    // pub fn step_in_at_end(&mut self) -> Option<Result<(), &'static str>> {
    //     match self.stack.last()?.create_child_iter_at_end(self.defs)? {
    //         Ok(iter) => {
    //             self.stack.push(iter);
    //         },

    //         Err(err) => return Some(Err(err)),
    //     }

    //     Some(Ok(()))
    // }

    pub fn step_over_forward(&mut self) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
        loop {
            match self.stack.last_mut()?.next(self.defs) {
                Some(item_ref) => {
                    return Some(item_ref);
                },

                None => {
                    self.step_out();
                },
            }
        }
    }

    // pub fn step_over_backward(&mut self) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
    //     match self.stack.last_mut()?.prev(self.defs) {
    //         Some(_) => {
    //             while let Some(_) = self.step_in_at_end() {}
    //         },

    //         None => {
    //             self.step_out();
    //         },
    //     }

    //     self.stack.last()?.peek(self.defs)
    // }

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


impl<'a> Iterator for DefViewCursor<'a> {
    type Item = DefViewItemRef<'a>;

    fn next(&mut self) -> Option<Self::Item> {
        self.step_forward().map(|res| res.unwrap())
    }
}


#[cfg(test)]
mod test {
    use super::*;


}