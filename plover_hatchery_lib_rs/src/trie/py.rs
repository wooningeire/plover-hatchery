use pyo3::prelude::*;

use super::nondeterministictrie::{LookupResult, NondeterministicTrie, TriePath};
use super::transition::{TransitionCostInfo, TransitionKey};

/// Python wrapper for TransitionKey
#[pyclass]
#[pyo3(name = "TransitionKey")]
#[derive(Clone)]
pub struct PyTransitionKey {
    pub inner: TransitionKey,
}

#[pymethods]
impl PyTransitionKey {
    #[new]
    pub fn new(src_node_index: usize, key_id: Option<usize>, transition_index: usize) -> Self {
        Self {
            inner: TransitionKey::new(src_node_index, key_id, transition_index),
        }
    }

    #[getter]
    pub fn src_node_index(&self) -> usize {
        self.inner.src_node_index
    }

    #[getter]
    pub fn key_id(&self) -> Option<usize> {
        self.inner.key_id
    }

    #[getter]
    pub fn transition_index(&self) -> usize {
        self.inner.transition_index
    }
}

/// Python wrapper for TriePath
#[pyclass]
#[pyo3(name = "TriePath")]
#[derive(Clone)]
pub struct PyTriePath {
    pub inner: TriePath,
}

#[pymethods]
impl PyTriePath {
    #[new]
    #[pyo3(signature = (dst_node_id=0, transitions=vec![]))]
    pub fn new(dst_node_id: usize, transitions: Vec<PyTransitionKey>) -> Self {
        Self {
            inner: TriePath::new(
                dst_node_id,
                transitions.into_iter().map(|t| t.inner).collect(),
            ),
        }
    }

    #[getter]
    pub fn dst_node_id(&self) -> usize {
        self.inner.dst_node_id
    }

    #[getter]
    pub fn transitions(&self) -> Vec<PyTransitionKey> {
        self.inner
            .transitions
            .iter()
            .map(|t| PyTransitionKey { inner: *t })
            .collect()
    }
}

/// Python wrapper for LookupResult
#[pyclass]
#[pyo3(name = "LookupResult")]
#[derive(Clone)]
pub struct PyLookupResult {
    pub inner: LookupResult,
}

#[pymethods]
impl PyLookupResult {
    #[new]
    pub fn new(translation_id: usize, cost: f64, transitions: Vec<PyTransitionKey>) -> Self {
        Self {
            inner: LookupResult::new(
                translation_id,
                cost,
                transitions.into_iter().map(|t| t.inner).collect(),
            ),
        }
    }

    #[getter]
    pub fn translation_id(&self) -> usize {
        self.inner.translation_id
    }

    #[getter]
    pub fn cost(&self) -> f64 {
        self.inner.cost
    }

    #[getter]
    pub fn transitions(&self) -> Vec<PyTransitionKey> {
        self.inner
            .transitions
            .iter()
            .map(|t| PyTransitionKey { inner: *t })
            .collect()
    }
}

/// Python wrapper for NondeterministicTrie
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

    /// Follow a transition from a source node, creating it if necessary.
    pub fn follow(
        &mut self,
        src_node_id: usize,
        key_id: Option<usize>,
        cost: f64,
        translation_id: usize,
    ) -> PyTriePath {
        let cost_info = TransitionCostInfo::new(cost, translation_id);
        let path = self.trie.follow(src_node_id, key_id, &cost_info);
        PyTriePath { inner: path }
    }

    /// Follow a chain of transitions from a source node.
    pub fn follow_chain(
        &mut self,
        src_node_id: usize,
        key_ids: Vec<Option<usize>>,
        cost: f64,
        translation_id: usize,
    ) -> PyTriePath {
        let cost_info = TransitionCostInfo::new(cost, translation_id);
        let path = self.trie.follow_chain(src_node_id, &key_ids, &cost_info);
        PyTriePath { inner: path }
    }

    /// Link a source node to an existing destination node.
    pub fn link(
        &mut self,
        src_node_id: usize,
        dst_node_id: usize,
        key_id: Option<usize>,
        cost: f64,
        translation_id: usize,
    ) -> PyTransitionKey {
        let cost_info = TransitionCostInfo::new(cost, translation_id);
        let key = self.trie.link(src_node_id, dst_node_id, key_id, &cost_info);
        PyTransitionKey { inner: key }
    }

    /// Follow a chain then link to an existing destination node.
    pub fn link_chain(
        &mut self,
        src_node_id: usize,
        dst_node_id: usize,
        key_ids: Vec<Option<usize>>,
        cost: f64,
        translation_id: usize,
    ) -> Vec<PyTransitionKey> {
        let cost_info = TransitionCostInfo::new(cost, translation_id);
        self.trie
            .link_chain(src_node_id, dst_node_id, &key_ids, &cost_info)
            .into_iter()
            .map(|t| PyTransitionKey { inner: t })
            .collect()
    }

    /// Set a translation at a node.
    pub fn set_translation(&mut self, node_id: usize, translation_id: usize) {
        self.trie.set_translation(node_id, translation_id);
    }

    /// Traverse from source paths following a key.
    pub fn traverse(&self, src_node_paths: Vec<PyTriePath>, key_id: Option<usize>) -> Vec<PyTriePath> {
        let paths = src_node_paths.into_iter().map(|p| p.inner);
        self.trie
            .traverse(paths, key_id)
            .map(|p| PyTriePath { inner: p })
            .collect()
    }

    /// Traverse from source paths following a chain of keys.
    pub fn traverse_chain(
        &self,
        src_node_paths: Vec<PyTriePath>,
        key_ids: Vec<Option<usize>>,
    ) -> Vec<PyTriePath> {
        let paths = src_node_paths.into_iter().map(|p| p.inner);
        self.trie
            .traverse_chain(paths, &key_ids)
            .map(|p| PyTriePath { inner: p })
            .collect()
    }

    /// Get translations and costs for a single node.
    pub fn get_translations_and_costs_single(
        &self,
        node_id: usize,
        transitions: Vec<PyTransitionKey>,
    ) -> Vec<(usize, f64)> {
        let transition_keys: Vec<_> = transitions.iter().map(|t| t.inner).collect();
        self.trie.get_translations_and_costs_single(node_id, &transition_keys)
    }

    /// Get translations and costs for multiple paths.
    pub fn get_translations_and_costs(&self, node_paths: Vec<PyTriePath>) -> Vec<PyLookupResult> {
        let paths = node_paths.into_iter().map(|p| p.inner);
        self.trie
            .get_translations_and_costs(paths)
            .map(|r| PyLookupResult { inner: r })
            .collect()
    }

    /// Get the cost of a specific transition for a translation.
    pub fn get_transition_cost(
        &self,
        transition: &PyTransitionKey,
        translation_id: usize,
    ) -> Option<f64> {
        self.trie.get_transition_cost(&transition.inner, translation_id)
    }

    /// Check if a transition has a specific key.
    pub fn transition_has_key(&self, transition: &PyTransitionKey, key_id: Option<usize>) -> bool {
        self.trie.transition_has_key(&transition.inner, key_id)
    }

    /// Get translations with minimum costs for each translation_id.
    pub fn get_translations_and_min_costs(&self, node_paths: Vec<PyTriePath>) -> Vec<PyLookupResult> {
        let paths = node_paths.into_iter().map(|p| p.inner);
        self.trie
            .get_translations_and_min_costs(paths)
            .into_iter()
            .map(|r| PyLookupResult { inner: r })
            .collect()
    }

    /// Get all translation IDs that have been set.
    pub fn get_all_translation_ids(&self) -> Vec<usize> {
        self.trie.get_all_translation_ids()
    }

    /// Get the number of nodes in the trie.
    pub fn n_nodes(&self) -> usize {
        self.trie.n_nodes()
    }

    /// Check if a transition has a cost for a specific translation.
    pub fn transition_has_cost_for_translation(
        &self,
        src_node_id: usize,
        key_id: Option<usize>,
        transition_index: usize,
        translation_id: usize,
    ) -> bool {
        self.trie.transition_has_cost_for_translation(src_node_id, key_id, transition_index, translation_id)
    }

    /// The root node constant.
    #[classattr]
    const ROOT: usize = NondeterministicTrie::ROOT;

    /// Create a reverse index for efficient reverse lookups.
    pub fn create_reverse_index(&self) -> PyReverseTrieIndex {
        PyReverseTrieIndex {
            reverse_nodes: self.trie.reversed_nodes(),
            reverse_translations: self.trie.reversed_translations(),
        }
    }
}

/// Helper struct for reverse lookups.
#[pyclass]
#[pyo3(name = "ReverseTrieIndex")]
pub struct PyReverseTrieIndex {
    reverse_nodes: crate::trie::nondeterministictrie::ReverseNodes,
    reverse_translations: crate::trie::nondeterministictrie::ReverseTranslations,
}

#[pymethods]
impl PyReverseTrieIndex {
    #[pyo3(signature = (trie, translation_id))]
    fn get_sequences(&self, trie: &PyNondeterministicTrie, translation_id: usize) -> Vec<PyLookupResult> {
        let rs_results = trie.trie.get_reverse_lookup_results(&self.reverse_nodes, &self.reverse_translations, translation_id);
        rs_results.into_iter().map(|r| PyLookupResult { inner: r }).collect()
    }

    #[pyo3(signature = (trie, translation_id))]
    fn get_subtrie_data(
        &self,
        py: Python<'_>,
        trie: &PyNondeterministicTrie,
        translation_id: usize,
    ) -> Option<PyObject> {
        // First get the raw data from Rust
        let subtrie_data = trie.trie.get_subtrie_data(
            &self.reverse_nodes,
            &self.reverse_translations,
            translation_id
        )?;

        // Now convert to Python objects
        let result_dict = pyo3::types::PyDict::new(py);
        
        // "nodes": tuple(nodes_toposort)
        result_dict.set_item("nodes", subtrie_data.nodes).ok()?;
        
        // "translation_nodes": reverse_translations[translation_id]
        result_dict.set_item("translation_nodes", subtrie_data.translation_nodes).ok()?;
         
        let transitions_list = pyo3::types::PyList::empty(py);
        for t in subtrie_data.transitions {
             let t_dict = pyo3::types::PyDict::new(py);
             t_dict.set_item("src_node_id", t.src_node_id).ok()?;
             t_dict.set_item("dst_node_id", t.dst_node_id).ok()?;
             t_dict.set_item("key_infos", t.key_infos).ok()?;
             transitions_list.append(t_dict).ok()?;
        }
        result_dict.set_item("transitions", transitions_list).ok()?;
        
        Some(result_dict.into())
    }
}
