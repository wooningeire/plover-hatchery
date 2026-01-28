/// Identifies a specific transition in the trie.
/// A transition goes from a source node to a destination node via a key.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct TransitionKey {
    pub src_node_index: usize,
    pub key_id: Option<usize>,
    pub transition_index: usize,
}

impl TransitionKey {
    pub fn new(src_node_index: usize, key_id: Option<usize>, transition_index: usize) -> Self {
        Self {
            src_node_index,
            key_id,
            transition_index,
        }
    }
}

/// Identifies a transition for a specific translation.
/// Used as a key in the transition_costs HashMap.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct TransitionCostKey {
    pub transition_key: TransitionKey,
    pub translation_id: usize,
}

impl TransitionCostKey {
    pub fn new(transition_key: TransitionKey, translation_id: usize) -> Self {
        Self {
            transition_key,
            translation_id,
        }
    }
}

/// Cost information associated with a transition during trie construction.
#[derive(Clone, Copy, Debug)]
pub struct TransitionCostInfo {
    pub cost: f64,
    pub translation_id: usize,
}

impl TransitionCostInfo {
    pub fn new(cost: f64, translation_id: usize) -> Self {
        Self {
            cost,
            translation_id,
        }
    }
}