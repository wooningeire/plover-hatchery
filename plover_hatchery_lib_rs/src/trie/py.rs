use pyo3::prelude::*;

use super::nondeterministictrie::NondeterministicTrie;

#[pyclass]
#[pyo3(name = "NondeterministicTrie")]
pub struct PyNondeterministicTrie {
    pub trie: Box<NondeterministicTrie>,
}

#[pymethods]
impl PyNondeterministicTrie {
    #[new]
    pub fn new() -> Self {
        Self {
            trie: Box::new(NondeterministicTrie::new()),
        }
    }
}
