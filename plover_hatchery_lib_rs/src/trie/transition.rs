use pyo3::prelude::*;

/// Identifies a specific transition in the trie.
/// A transition goes from a source node to a destination node via a key.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
#[pyclass]
pub struct TransitionKey {
    #[pyo3(get, set)]
    pub src_node_index: usize,
    #[pyo3(get, set)]
    pub key_id: Option<usize>,
    #[pyo3(get, set)]
    pub transition_index: usize,
}

#[pymethods]
impl TransitionKey {
    #[new]
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
#[pyclass]
pub struct TransitionCostKey {
    #[pyo3(get, set)]
    pub transition_key: TransitionKey,
    #[pyo3(get, set)]
    pub translation_id: usize,
}

#[pymethods]
impl TransitionCostKey {
    #[new]
    pub fn new(transition_key: TransitionKey, translation_id: usize) -> Self {
        Self {
            transition_key,
            translation_id,
        }
    }
}

/// Cost information associated with a transition during trie construction.
#[derive(Clone, Copy, Debug)]
#[pyclass]
pub struct TransitionCostInfo {
    #[pyo3(get, set)]
    pub cost: f64,
    #[pyo3(get, set)]
    pub translation_id: usize,
}

#[pymethods]
impl TransitionCostInfo {
    #[new]
    pub fn new(cost: f64, translation_id: usize) -> Self {
        Self {
            cost,
            translation_id,
        }
    }
}