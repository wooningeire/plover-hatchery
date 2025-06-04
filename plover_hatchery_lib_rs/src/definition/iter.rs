use std::{cell::RefCell, rc::Rc};

use super::*;


#[derive(Clone)]
pub struct StackItem<'a> {
    pub index: usize,
    pub item: DefViewItem<'a>,
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

#[derive(Clone)]
pub enum StepData<'a> {
    In(StackItem<'a>),
    Over(StackItem<'a>),
    Out,
}

pub struct DefViewCursor<'a> {
    defs: &'a DefDict,
    pub stack: Vec<StackItem<'a>>,
}

impl<'a> DefViewCursor<'a> {
    pub fn new(view: &'a DefView<'a>) -> Self {
        DefViewCursor {
            defs: view.defs,

            stack: vec![StackItem {
                index: 0,
                item: view.root.as_item(),
            }],
        }
    }


    pub fn next_step_data(&self) -> Option<StepData<'a>> {
        let tip = self.stack.last()?;

        // First attempt to step in from the tip
        if let Some(inner) = tip.get(0, self.defs) {
            return Some(StepData::In(StackItem::new(0, inner)));
        }

        // Next attempt to step over
        let parent = if self.stack.len() >= 2 { &self.stack[self.stack.len() - 2] } else { return None };


        let new_tip_index = tip.index + 1;
        if let Some(inner) = parent.get(new_tip_index, self.defs) {
            return Some(StepData::Over(StackItem::new(new_tip_index, inner)));
        }

        // Finally attempt to step out
        Some(StepData::Out)
    }

    pub fn step_with_data(&mut self, data: &StepData<'a>) {
        match data {
            StepData::In(item) => {
                self.stack.push(item.clone());
            },

            StepData::Over(item) => {
                let last_index = self.stack.len() - 1;
                self.stack[last_index] = item.clone();
            },

            StepData::Out => {
                self.stack.pop();
            },
        }
    }

    pub fn step(&mut self) -> Option<StepData<'a>> {
        let data = self.next_step_data()?;
        self.step_with_data(&data);

        Some(data)
    }
}