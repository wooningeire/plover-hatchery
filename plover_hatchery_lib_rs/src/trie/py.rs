use pyo3::prelude::*;

use super::nondeterministic_trie::{LookupResult, NondeterministicTrie, TriePath, NodeSrc, JoinedTriePaths};
use super::transition::{TransitionCostInfo, TransitionKey};


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
    ) -> TriePath {
        let cost_info = TransitionCostInfo::new(cost, translation_id);
        let path = self.trie.follow(src_node_id, key_id, &cost_info);
        path
    }

    /// Follow a chain of transitions from a source node.
    pub fn follow_chain(
        &mut self,
        src_node_id: usize,
        key_ids: Vec<Option<usize>>,
        cost: f64,
        translation_id: usize,
    ) -> TriePath {
        let cost_info = TransitionCostInfo::new(cost, translation_id);
        let path = self.trie.follow_chain(src_node_id, &key_ids, &cost_info);
        path
    }

    /// Link a source node to an existing destination node.
    pub fn link(
        &mut self,
        src_node_id: usize,
        dst_node_id: usize,
        key_id: Option<usize>,
        cost: f64,
        translation_id: usize,
    ) -> TransitionKey {
        let cost_info = TransitionCostInfo::new(cost, translation_id);
        let key = self.trie.link(src_node_id, dst_node_id, key_id, &cost_info);
        key
    }

    /// Follow a chain then link to an existing destination node.
    pub fn link_chain(
        &mut self,
        src_node_id: usize,
        dst_node_id: usize,
        key_ids: Vec<Option<usize>>,
        cost: f64,
        translation_id: usize,
    ) -> Vec<TransitionKey> {
        let cost_info = TransitionCostInfo::new(cost, translation_id);
        self.trie.link_chain(src_node_id, dst_node_id, &key_ids, &cost_info)
    }

    /// Link multiple source nodes to a common destination node with a single key per source.
    pub fn link_join(
        &mut self,
        src_nodes: Vec<PyRef<NodeSrc>>,
        dst_node_id: Option<usize>,
        key_ids: Vec<Option<usize>>,
        translation_id: usize,
    ) -> JoinedTriePaths {
        let rs_src_nodes: Vec<NodeSrc> = src_nodes.iter().map(|s| (*s).clone()).collect();
        self.trie.link_join(&rs_src_nodes, dst_node_id, &key_ids, translation_id)
    }

    /// Link multiple source nodes to a common destination node with key chains per source.
    pub fn link_join_chain(
        &mut self,
        src_nodes: Vec<PyRef<NodeSrc>>,
        dst_node_id: Option<usize>,
        key_id_chains: Vec<Vec<Option<usize>>>,
        translation_id: usize,
    ) -> JoinedTriePaths {
        let rs_src_nodes: Vec<NodeSrc> = src_nodes.iter().map(|s| (*s).clone()).collect();
        self.trie.link_join_chain(&rs_src_nodes, dst_node_id, &key_id_chains, translation_id)
    }

    /// Set a translation at a node.
    pub fn set_translation(&mut self, node_id: usize, translation_id: usize) {
        self.trie.set_translation(node_id, translation_id);
    }

    /// Traverse from source paths following a key.
    pub fn traverse(&self, src_node_paths: Vec<TriePath>, key_id: Option<usize>) -> Vec<TriePath> {
        self.trie
            .traverse(src_node_paths.into_iter(), key_id)
            .collect()
    }

    /// Traverse from source paths following a chain of keys.
    pub fn traverse_chain(
        &self,
        src_node_paths: Vec<TriePath>,
        key_ids: Vec<Option<usize>>,
    ) -> Vec<TriePath> {
        self.trie
            .traverse_chain(src_node_paths.into_iter(), &key_ids)
            .collect()
    }

    /// Get translations and costs for a single node.
    pub fn get_translations_and_costs_single(
        &self,
        node_id: usize,
        transitions: Vec<TransitionKey>,
    ) -> Vec<(usize, f64)> {
        self.trie.get_translations_and_costs_single(node_id, &transitions)
    }

    /// Get translations and costs for multiple paths.
    pub fn get_translations_and_costs(&self, node_paths: Vec<TriePath>) -> Vec<LookupResult> {
        self.trie
            .get_translations_and_costs(node_paths.into_iter())
            .collect()
    }

    /// Get the cost of a specific transition for a translation.
    pub fn get_transition_cost(
        &self,
        transition: &TransitionKey,
        translation_id: usize,
    ) -> Option<f64> {
        self.trie.get_transition_cost(&transition, translation_id)
    }

    /// Check if a transition has a specific key.
    pub fn transition_has_key(&self, transition: &TransitionKey, key_id: Option<usize>) -> bool {
        self.trie.transition_has_key(transition, key_id)
    }

    /// Get translations with minimum costs for each translation_id.
    pub fn get_translations_and_min_costs(&self, node_paths: Vec<TriePath>) -> Vec<LookupResult> {
        self.trie.get_translations_and_min_costs(node_paths.into_iter())
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
    reverse_nodes: crate::trie::nondeterministic_trie::ReverseNodes,
    reverse_translations: crate::trie::nondeterministic_trie::ReverseTranslations,
}

#[pymethods]
impl PyReverseTrieIndex {
    #[pyo3(signature = (trie, translation_id))]
    fn get_sequences(&self, trie: &PyNondeterministicTrie, translation_id: usize) -> Vec<LookupResult> {
        trie.trie.get_reverse_lookup_results(&self.reverse_nodes, &self.reverse_translations, translation_id)
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
