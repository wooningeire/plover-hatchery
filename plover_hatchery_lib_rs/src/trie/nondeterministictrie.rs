use std::collections::HashMap;

use super::transition::SingleTranslationTransitionKey;

pub struct NondeterministicTrie {
    transitions: Vec<HashMap<Option<usize>, Vec<usize>>>,
    node_translations: HashMap<usize, Vec<usize>>,
    transition_costs: HashMap<SingleTranslationTransitionKey, f64>,
}

impl NondeterministicTrie {
    pub fn new() -> Self {
        Self {
            transitions: vec![HashMap::new()],
            node_translations: HashMap::new(),
            transition_costs: HashMap::new(),
        }
    }
}