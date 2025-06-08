use super::{
    view::{
        DefView,
        DefViewItemRef,
        DefViewErr,
    },
};

mod iter;
pub use iter::{
    DefViewItemRefChildrenCursor,
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

    pub fn of_view_at_end(view: &'view DefView<'defs>) -> Result<Self, DefViewErr> {
        let mut cursor = DefViewCursor {
            view,

            stack: vec![DefViewItemRefChildrenCursor::new_at_end(view.root().as_item_ref())],
        };

        cursor.drill_in_backward()?;

        Ok(cursor)
    }

    pub fn with_index_stack(view: &'view DefView<'defs>, mut indexes: impl Iterator<Item = Option<usize>>) -> Result<Option<Self>, DefViewErr> {
        let mut cursor = DefViewCursor {
            view,

            stack: match indexes.next() {
                Some(first_index) => vec![DefViewItemRefChildrenCursor::new(view.root().as_item_ref(), first_index)],

                None => vec![],
            },
        };

        for index in indexes {
            if !cursor.step_in_at(index)? {
                return Ok(None);
            }
        }

        Ok(Some(cursor))
    }

    pub fn peek(&self) -> Result<Option<DefViewItemRef<'defs>>, DefViewErr> {
        match self.stack.last() {
            Some(iter) => iter.peek(self.view.defs()),

            None => Ok(Some(self.view.root().as_item_ref())),
        }
    }

    pub fn step_forward(&mut self) -> Result<Option<DefViewItemRef<'defs>>, DefViewErr> {
        self.step_in_at_start()?;
        self.step_over_forward()
    }

    pub fn step_backward(&mut self) -> Result<Option<DefViewItemRef<'defs>>, DefViewErr> {
        match self.stack.last_mut() {
            Some(iter) => match iter.prev(self.view.defs())? {
                Some(_) => {
                    self.drill_in_backward()?;
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

    pub fn step_in_at_start(&mut self) -> Result<bool, DefViewErr> {
        match self.stack.last() {
            Some(iter) => match iter.create_child_iter_at_start(self.view.defs())? {
                Some(iter) => {
                    self.stack.push(iter);

                    Ok(true)
                },

                None => Ok(false)
            },

            None => Ok(false),
        }
    }

    pub fn step_in_at_end(&mut self) -> Result<bool, DefViewErr> {
        match self.stack.last() {
            Some(iter) => match iter.create_child_iter_at_end(self.view.defs())? {
                Some(iter) => {
                    self.stack.push(iter);

                    Ok(true)
                },

                None => Ok(false),
            },

            None => Ok(false),
        }
    }

    pub fn step_in_at(&mut self, index: Option<usize>) -> Result<bool, DefViewErr> {
        match self.stack.last() {
            Some(iter) => match iter.create_child_iter_at(self.view.defs(), index)? {
                Some(iter) => {
                    self.stack.push(iter);

                    Ok(true)
                },

                None => Ok(false),
            },

            None => Ok(false),
        }
    }

    pub fn step_over_forward(&mut self) -> Result<Option<DefViewItemRef<'defs>>, DefViewErr> {
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

    fn drill_in_backward(&mut self) -> Result<(), DefViewErr> {
        while self.step_in_at_end()? {}
        self.stack.pop(); // last index will be a None, which we don't want for backward traversal

        Ok(())
    }

    pub fn step_out(&mut self) {
        self.stack.pop();
    }

    pub fn indexes<'a>(&'a self) -> impl Iterator<Item = &'a usize> + 'a {
        self.stack.iter()
            .map(|iter| &iter.index)
            .take_while(|iter| iter.is_some())
            .map(|index| index.as_ref().unwrap())
    }

    pub fn index_stack(&self) -> Vec<usize> {
        self.indexes()
            .map(|index| *index)
            .collect::<Vec<_>>()
    }

    pub fn prev_keysymbol_cur(&self) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.view.last_index_before(
            self.clone(),
            |item_ref| match item_ref {
                DefViewItemRef::Keysymbol(_) => true,

                _ => false,
            },
        )
    }

    pub fn next_keysymbol_cur(&self) -> Result<Option<DefViewCursor>, DefViewErr> {
        self.view.first_index_after(
            self.clone(),
            |item_ref| match item_ref {
                DefViewItemRef::Keysymbol(_) => true,

                _ => false,
            },
        )
    }

    pub fn occurs_before(&self, cur: Option<DefViewCursor>) -> bool {
        match cur {
            Some(cur) => seq_less_than(self.indexes(), cur.indexes()),

            None => true,
        }
    }

    pub fn occurs_after(&self, cur: Option<DefViewCursor>) -> bool {
        match cur {
            Some(cur) => seq_less_than(cur.indexes(), self.indexes()),

            None => true,
        }
    }

    pub fn occurs_before_first_consonant(&self) -> Result<bool, DefViewErr> {
        Ok(self.occurs_before(self.view.first_consonant_cur()?))
    }

    pub fn occurs_after_last_consonant(&self) -> Result<bool, DefViewErr> {
        Ok(self.occurs_after(self.view.last_consonant_cur()?))
    }

    pub fn occurs_before_first_vowel(&self) -> Result<bool, DefViewErr> {
        Ok(self.occurs_before(self.view.first_vowel_cur()?))
    }

    pub fn occurs_after_last_vowel(&self) -> Result<bool, DefViewErr> {
        Ok(self.occurs_after(self.view.last_vowel_cur()?))
    }

    pub fn spelling_including_silent(&self) -> Result<String, DefViewErr> {
        let mut backward_parts = Vec::new();
        {
            let mut cur = self.clone();
            while let Some(item_ref) = cur.step_backward()? {
                match item_ref {
                    DefViewItemRef::Sopheme(sopheme) => {
                        if !sopheme.can_be_silent() {
                            break;
                        }

                        backward_parts.push(sopheme.chars.as_str());
                    },

                    _ => {},
                }
            }

        };
        

        let mut all_parts = backward_parts.into_iter()
            .rev()
            .collect::<Vec<_>>();

        
        match self.peek()? {
            Some(DefViewItemRef::Sopheme(sopheme)) => {
                all_parts.push(sopheme.chars.as_str());
            },

            Some(_) => {},

            None => return Err(DefViewErr::UnexpectedNone),
        }


        {
            let mut cur = self.clone();
            while let Some(item_ref) = cur.step_forward()? {
                match item_ref {
                    DefViewItemRef::Sopheme(sopheme) => {
                        if !sopheme.can_be_silent() {
                            break;
                        }

                        all_parts.push(sopheme.chars.as_str());
                    },

                    _ => {},
                }
            }
        }

        Ok(all_parts.join(""))
    }
}

pub fn seq_less_than<'a>(seq_a: impl Iterator<Item = &'a usize>, mut seq_b: impl Iterator<Item = &'a usize>) -> bool {
    for a in seq_a {
        if let Some(b) = seq_b.next() {
            if a < b {
                return true;
            }

            if a > b {
                return false;
            }
        } else {
            return false; // seq_a is longer than seq_b
        }
    }

    if let Some(_) = seq_b.next() {
        true // seq_a is shorter than seq_b
    } else {
        false // seq_a is the same length as seq_b
    }
}


// #[cfg(test)]
// mod test {
//     use super::*;


// }