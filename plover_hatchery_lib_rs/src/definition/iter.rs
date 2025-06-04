use std::{cell::RefCell, rc::Rc};

use super::*;


#[derive(Clone)]
pub struct StackItem<'a> {
    index: usize,
    item: DefViewItem<'a>,
}


impl<'a> StackItem<'a> {
    pub fn new(index: usize, item: DefViewItem<'a>) -> Self {
        StackItem {
            index,
            item,
        }
    }

    pub fn get(&self, index: usize, defs: &'a DefDict) -> Option<DefViewItem<'a>> {
        self.item.get(index, defs)
            .ok()
            .and_then(|inner| inner)
    }
}

enum StepData<'a> {
    In(StackItem<'a>),
    Over(StackItem<'a>),
    Out,
}

#[pyclass]
enum StepDir {
    In,
    Over,
    Out,
}

pub struct DefViewCursor<'a> {
    defs: &'a DefDict,
    stack: RefCell<Vec<StackItem<'a>>>,
}

impl<'a> DefViewCursor<'a> {
    pub fn new(view: &'a DefView<'a>) -> Self {
        DefViewCursor {
            defs: view.defs,

            stack: RefCell::new(vec![StackItem {
                index: 0,
                item: view.root.as_item(),
            }]),
        }
    }


    fn next_step_data(&'a self) -> Option<StepData<'a>> {
        let stack = self.stack.borrow();

        let tip = stack.last()?;

        // First attempt to step in from the tip
        if let Some(inner) = tip.get(0, self.defs) {
            return Some(StepData::In(StackItem::new(0, inner)));
        }

        // Next attempt to step over
        let parent = if stack.len() >= 2 { &stack[stack.len() - 2] } else { return None };


        let new_tip_index = tip.index + 1;
        if let Some(inner) = parent.get(new_tip_index, self.defs) {
            return Some(StepData::Over(StackItem::new(new_tip_index, inner)));
        }

        // Finally attempt to step out
        Some(StepData::Out)
    }

    pub fn step(&'a mut self) -> Option<StepDir> {
        let data = self.next_step_data()?;

        let mut stack = self.stack.borrow_mut();

        match data {
            StepData::In(item) => {
                stack.push(item);
                Some(StepDir::In)
            },

            StepData::Over(item) => {
                let last_index = stack.len() - 1;
                stack[last_index] = item;
                Some(StepDir::Over)
            },

            StepData::Out => {
                stack.pop();
                Some(StepDir::Out)
            },
        }
    }
}