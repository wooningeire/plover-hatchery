use pyo3::prelude::*;

#[pyclass]
pub struct TransitionSourceNode {
    #[pyo3(get, set)]
    pub src_node_index: usize,
    #[pyo3(get, set)]
    pub outgoing_cost: f64,
    #[pyo3(get, set)]
    pub outgoing_transition_flags: Vec<usize>,
}

#[pymethods]
impl TransitionSourceNode {
    #[new]
    pub fn new(src_node_index: usize, outgoing_cost: f64, outgoing_transition_flags: Vec<usize>) -> Self {
        Self {
            src_node_index,
            outgoing_cost,
            outgoing_transition_flags,
        }
    }

    #[staticmethod]
    pub fn root() -> Self {
        Self {
            src_node_index: 0,
            outgoing_cost: 0.0,
            outgoing_transition_flags: vec![],
        }
    }
}