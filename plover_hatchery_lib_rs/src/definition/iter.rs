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
    Over(usize, StackItem<'a>),
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
        let mut tip = self.stack.last()?;

        // First attempt to step in from the tip
        if let Some(inner) = tip.get(0, self.defs) {
            return Some(StepData::In(StackItem::new(0, inner)));
        }

        // Finally attempt to step out
        // Next attempt to step ove
        if self.stack.len() < 2 {
            return None;
        }

        let mut parent_index = self.stack.len() - 2;

        loop {
            let parent = &self.stack[parent_index];
            
            let new_tip_index = tip.index + 1;
            if let Some(inner) = parent.get(new_tip_index, self.defs) {
                return Some(StepData::Over(parent_index + 1, StackItem::new(new_tip_index, inner)));
            }

            if parent_index == 0 {
                return None;
            }

            tip = parent;
            parent_index -= 1;
        }
    }

    pub fn step_with_data(&mut self, data: &StepData<'a>) {
        match data {
            StepData::In(item) => {
                self.stack.push(item.clone());
            },

            StepData::Over(n_levels_to_keep, item) => {
                while self.stack.len() > *n_levels_to_keep {
                    self.stack.pop();
                }
                self.stack.push(item.clone());
            },
        }
    }

    pub fn step(&mut self) -> Option<StepData<'a>> {
        let data = self.next_step_data()?;
        self.step_with_data(&data);

        Some(data)
    }
}


#[cfg(test)]
mod test {
    use super::*;


}