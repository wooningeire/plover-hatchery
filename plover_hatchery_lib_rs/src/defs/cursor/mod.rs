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
    pub fn of_view<'b>(view: &'b DefView<'a>) -> Self
        where 'b: 'a
    {
        DefViewCursor {
            defs: view.defs(),

            stack: vec![DefViewItemRefChildrenCursor::new(view.root().as_item())],
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

        self.step_over()
    }

    pub fn step_over(&mut self) -> Option<Result<DefViewItemRef<'a>, &'static str>> {
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

    pub fn index_stack(&self) -> Vec<usize> {
        self.stack.iter()
            .map(|iter| iter.index().unwrap_or(0))
            .collect::<Vec<_>>()
    }
}


#[cfg(test)]
mod test {
    use super::*;


}