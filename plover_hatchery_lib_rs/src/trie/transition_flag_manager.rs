use std::collections::HashMap;

use pyo3::prelude::*;

use super::transition_flag::TransitionFlag;
use super::transition::TransitionCostKey;

#[derive(Debug, Clone)]
#[pyclass]
pub struct TransitionFlagManager {
    pub mappings: HashMap<TransitionCostKey, Vec<usize>>,
    pub flag_types: Vec<TransitionFlag>,
}

impl TransitionFlagManager {
    pub fn flag_transition(&mut self, transition_cost_key: TransitionCostKey, flag_index: usize) {
        self.mappings.entry(transition_cost_key)
            .or_default()
            .push(flag_index);
    }
}

#[pymethods]
impl TransitionFlagManager {
    #[new]
    pub fn new() -> Self {
        Self {
            mappings: HashMap::new(),
            flag_types: Vec::new(),
        }
    }

    pub fn new_flag(&mut self, label: String) -> usize {
        let flag = TransitionFlag::new(label);
        self.flag_types.push(flag.clone());
        self.flag_types.len() - 1
    }

    #[pyo3(name = "flag_transition")]
    pub fn flag_transition_py(&mut self, transition_cost_key: Py<TransitionCostKey>, flag_index: usize, py: Python<'_>) {
        self.flag_transition(*transition_cost_key.borrow(py), flag_index);
    }

    pub fn get_label(&self, flag_index: usize) -> &str {
        &self.flag_types[flag_index].label
    }

    pub fn get_flags(&self, transition_cost_key: TransitionCostKey) -> Vec<usize> {
        self.mappings.get(&transition_cost_key)
            .cloned()
            .unwrap_or_default()
    }
}
