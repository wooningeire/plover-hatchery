use pyo3::prelude::*;

#[derive(Clone, Debug)]
pub enum TransitionKey {
    Empty,
    String(String),
}

#[pyclass]
#[derive(Clone, Debug)]
pub struct NondeterministicTrie {
    
}