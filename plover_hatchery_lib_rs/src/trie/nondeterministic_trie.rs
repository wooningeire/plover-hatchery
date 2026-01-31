use std::collections::{HashMap, HashSet};

use pyo3::prelude::*;

use super::transition::{TransitionCostInfo, TransitionCostKey, TransitionKey};

/// A path through the trie, tracking the destination node and transitions taken.
#[derive(Clone, Debug)]
#[pyclass]
pub struct TriePath {
    #[pyo3(get, set)]
    pub dst_node_id: usize,
    #[pyo3(get, set)]
    pub transitions: Vec<TransitionKey>,
}

#[pymethods]
impl TriePath {
    #[new]
    pub fn new(dst_node_id: usize, transitions: Vec<TransitionKey>) -> Self {
        Self {
            dst_node_id,
            transitions,
        }
    }

    #[staticmethod]
    pub fn root() -> Self {
        Self {
            dst_node_id: 0,
            transitions: Vec::new(),
        }
    }
}

/// Result of a translation lookup.
#[derive(Clone, Debug)]
#[pyclass]
pub struct LookupResult {
    #[pyo3(get, set)]
    pub translation_id: usize,
    #[pyo3(get, set)]
    pub cost: f64,
    #[pyo3(get, set)]
    pub transitions: Vec<TransitionKey>,
}

#[pymethods]
impl LookupResult {
    #[new]
    pub fn new(translation_id: usize, cost: f64, transitions: Vec<TransitionKey>) -> Self {
        Self {
            translation_id,
            cost,
            transitions,
        }
    }
}

pub type ReverseNodes = HashMap<usize, HashMap<Option<usize>, Vec<(usize, usize)>>>;
pub type ReverseTranslations = HashMap<usize, Vec<usize>>;

#[derive(Clone, Debug)]
pub struct SubtrieTransition {
    pub src_node_id: usize,
    pub dst_node_id: usize,
    pub key_infos: Vec<(Option<usize>, usize, f64)>,
}

#[derive(Clone, Debug)]
pub struct SubtrieData {
    pub nodes: Vec<usize>,
    pub transitions: Vec<SubtrieTransition>,
    pub translation_nodes: Vec<usize>,
}

/// A nondeterministic trie that can be in multiple states at once.
/// Used for efficient lookup of stenographic translations.
pub struct NondeterministicTrie {
    /// Mapping from each node's id to its lists of destination nodes, based on the keys' ids
    transitions: Vec<HashMap<Option<usize>, Vec<usize>>>,
    /// Mapping from each node's id to its list of translation ids
    node_translations: HashMap<usize, Vec<usize>>,
    /// Costs associated with each (transition, translation) pair
    transition_costs: HashMap<TransitionCostKey, f64>,
    /// Tracks which nodes have been used by each translation during construction
    used_nodes_by_translation: HashMap<usize, HashSet<usize>>,
}

/// A source node with associated cost and outgoing transition flags.
/// Used for building trie entries from multiple starting points.
#[derive(Clone, Debug)]
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
    #[pyo3(signature = (src_node_index, outgoing_cost=0.0, outgoing_transition_flags=vec![]))]
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

    /// Creates copies of source nodes with incremented costs.
    #[staticmethod]
    pub fn increment_costs(srcs: Vec<TransitionSourceNode>, cost_change: f64) -> Vec<TransitionSourceNode> {
        srcs.into_iter()
            .map(|src| TransitionSourceNode {
                src_node_index: src.src_node_index,
                outgoing_cost: src.outgoing_cost + cost_change,
                outgoing_transition_flags: src.outgoing_transition_flags,
            })
            .collect()
    }

    /// Creates copies of source nodes with additional flags.
    #[staticmethod]
    pub fn add_flags(srcs: Vec<TransitionSourceNode>, flags: Vec<usize>) -> Vec<TransitionSourceNode> {
        srcs.into_iter()
            .map(|src| {
                let mut new_flags = src.outgoing_transition_flags.clone();
                new_flags.extend(flags.iter());
                TransitionSourceNode {
                    src_node_index: src.src_node_index,
                    outgoing_cost: src.outgoing_cost,
                    outgoing_transition_flags: new_flags,
                }
            })
            .collect()
    }
}

/// A sequence of transitions created by a join operation.
#[derive(Clone, Debug)]
#[pyclass]
pub struct JoinedTransitionSeq {
    #[pyo3(get, set)]
    pub transitions: Vec<TransitionKey>,
}

#[pymethods]
impl JoinedTransitionSeq {
    #[new]
    pub fn new(transitions: Vec<TransitionKey>) -> Self {
        Self { transitions }
    }
}

/// Result of a link_join operation, containing the destination node and all transition sequences.
#[derive(Clone, Debug)]
#[pyclass]
pub struct JoinedTriePaths {
    #[pyo3(get, set)]
    pub dst_node_id: Option<usize>,
    #[pyo3(get, set)]
    pub transition_seqs: Vec<JoinedTransitionSeq>,
}

#[pymethods]
impl JoinedTriePaths {
    #[new]
    pub fn new(dst_node_id: Option<usize>, transition_seqs: Vec<JoinedTransitionSeq>) -> Self {
        Self {
            dst_node_id,
            transition_seqs,
        }
    }
}

impl NondeterministicTrie {
    pub const ROOT: usize = 0;

    pub fn new() -> Self {
        Self {
            transitions: vec![HashMap::new()],
            node_translations: HashMap::new(),
            transition_costs: HashMap::new(),
            used_nodes_by_translation: HashMap::new(),
        }
    }

    /// Creates a new node and returns its id.
    fn create_new_node(&mut self) -> usize {
        let new_node_id = self.transitions.len();
        self.transitions.push(HashMap::new());
        new_node_id
    }

    /// Assigns a cost to a transition for a specific translation.
    fn assign_transition_cost(
        &mut self,
        src_node_id: usize,
        key_id: Option<usize>,
        transition_index: usize,
        cost_info: &TransitionCostInfo,
    ) {
        let cost_key = TransitionCostKey::new(
            TransitionKey::new(src_node_id, key_id, transition_index),
            cost_info.translation_id,
        );
        let existing_cost = self.transition_costs.get(&cost_key).copied().unwrap_or(f64::INFINITY);
        self.transition_costs.insert(cost_key, cost_info.cost.min(existing_cost));
    }

    /// Gets the destination node by following an existing transition or creates it if it doesn't exist.
    pub fn follow(
        &mut self,
        src_node_id: usize,
        key_id: Option<usize>,
        cost_info: &TransitionCostInfo,
    ) -> TriePath {
        let translation_id = cost_info.translation_id;
        
        // Get or create the used nodes set for this translation
        let used_nodes = self.used_nodes_by_translation
            .entry(translation_id)
            .or_insert_with(HashSet::new);

        // Check if there's an existing transition we can reuse
        if let Some(dst_node_ids) = self.transitions[src_node_id].get(&key_id) {
            for (transition_index, &dst_node_id) in dst_node_ids.iter().enumerate() {
                if used_nodes.contains(&dst_node_id) {
                    continue;
                }

                // Found a reusable node
                used_nodes.insert(dst_node_id);
                self.assign_transition_cost(src_node_id, key_id, transition_index, cost_info);
                return TriePath::new(
                    dst_node_id,
                    vec![TransitionKey::new(src_node_id, key_id, transition_index)],
                );
            }
        }

        // Create a new node
        let new_node_id = self.create_new_node();
        self.used_nodes_by_translation
            .entry(translation_id)
            .or_insert_with(HashSet::new)
            .insert(new_node_id);

        let new_transition_index = self.transitions[src_node_id]
            .get(&key_id)
            .map(|v| v.len())
            .unwrap_or(0);

        self.transitions[src_node_id]
            .entry(key_id)
            .or_insert_with(Vec::new)
            .push(new_node_id);

        self.assign_transition_cost(src_node_id, key_id, new_transition_index, cost_info);

        TriePath::new(
            new_node_id,
            vec![TransitionKey::new(src_node_id, key_id, new_transition_index)],
        )
    }

    /// Follows a chain of keys from a source node.
    pub fn follow_chain(
        &mut self,
        src_node_id: usize,
        key_ids: &[Option<usize>],
        cost_info: &TransitionCostInfo,
    ) -> TriePath {
        let mut current_node = src_node_id;
        let mut all_transitions = Vec::new();

        for (i, &key_id) in key_ids.iter().enumerate() {
            let path_addend = if i == key_ids.len() - 1 {
                // Only assign the full cost to the last transition
                self.follow(current_node, key_id, cost_info)
            } else {
                // Assign zero cost to intermediate transitions
                self.follow(
                    current_node,
                    key_id,
                    &TransitionCostInfo::new(0.0, cost_info.translation_id),
                )
            };

            current_node = path_addend.dst_node_id;
            all_transitions.extend(path_addend.transitions);
        }

        TriePath::new(current_node, all_transitions)
    }

    /// Creates a transition from a source node to an existing destination node.
    pub fn link(
        &mut self,
        src_node_id: usize,
        dst_node_id: usize,
        key_id: Option<usize>,
        cost_info: &TransitionCostInfo,
    ) -> TransitionKey {
        let dst_dict = &mut self.transitions[src_node_id];

        let transition_index = if let Some(dst_node_ids) = dst_dict.get(&key_id) {
            if let Some(idx) = dst_node_ids.iter().position(|&id| id == dst_node_id) {
                // Already exists
                idx
            } else {
                // Add new link
                let idx = dst_node_ids.len();
                dst_dict.get_mut(&key_id).unwrap().push(dst_node_id);
                idx
            }
        } else {
            // Create new entry
            dst_dict.insert(key_id, vec![dst_node_id]);
            0
        };

        self.assign_transition_cost(src_node_id, key_id, transition_index, cost_info);
        self.used_nodes_by_translation
            .entry(cost_info.translation_id)
            .or_insert_with(HashSet::new)
            .insert(dst_node_id);

        TransitionKey::new(src_node_id, key_id, transition_index)
    }

    /// Follows all but the final transition, then links to the destination node.
    pub fn link_chain(
        &mut self,
        src_node_id: usize,
        dst_node_id: usize,
        key_ids: &[Option<usize>],
        cost_info: &TransitionCostInfo,
    ) -> Vec<TransitionKey> {
        if key_ids.is_empty() {
            return Vec::new();
        }

        let path = self.follow_chain(
            src_node_id,
            &key_ids[..key_ids.len() - 1],
            &TransitionCostInfo::new(0.0, cost_info.translation_id),
        );

        let transition = self.link(
            path.dst_node_id,
            dst_node_id,
            key_ids[key_ids.len() - 1],
            cost_info,
        );

        let mut transitions = path.transitions;
        transitions.push(transition);
        transitions
    }

    /// Links multiple source nodes to a common destination node with a single key per source.
    /// If dst_node_id is None, creates a new destination node from the first source.
    /// Returns the destination node and all transition sequences created.
    pub fn link_join(
        &mut self,
        src_nodes: &[TransitionSourceNode],
        dst_node_id: Option<usize>,
        key_ids: &[Option<usize>],
        translation_id: usize,
    ) -> JoinedTriePaths {
        self.link_join_chain(
            src_nodes,
            dst_node_id,
            &key_ids.iter().map(|k| vec![*k]).collect::<Vec<_>>(),
            translation_id,
        )
    }

    /// Links multiple source nodes to a common destination node with key chains per source.
    /// If dst_node_id is None, creates a new destination node from the first source.
    /// Returns the destination node and all transition sequences created.
    pub fn link_join_chain(
        &mut self,
        src_nodes: &[TransitionSourceNode],
        dst_node_id: Option<usize>,
        key_id_chains: &[Vec<Option<usize>>],
        translation_id: usize,
    ) -> JoinedTriePaths {
        if src_nodes.is_empty() || key_id_chains.is_empty() {
            return JoinedTriePaths {
                dst_node_id: None,
                transition_seqs: Vec::new(),
            };
        }

        // Build all (src_node, key_chain) pairs
        let mut pairs: Vec<(&TransitionSourceNode, &Vec<Option<usize>>)> = Vec::new();
        for src_node in src_nodes {
            for key_chain in key_id_chains {
                pairs.push((src_node, key_chain));
            }
        }

        if pairs.is_empty() {
            return JoinedTriePaths {
                dst_node_id: None,
                transition_seqs: Vec::new(),
            };
        }

        let mut transition_seqs: Vec<JoinedTransitionSeq> = Vec::new();

        // If dst_node_id is None, create it from the first pair
        let actual_dst_node_id = if let Some(dst) = dst_node_id {
            dst
        } else {
            let (first_src, first_keys) = pairs[0];
            let cost_info = TransitionCostInfo::new(first_src.outgoing_cost, translation_id);
            let first_path = self.follow_chain(first_src.src_node_index, first_keys, &cost_info);
            transition_seqs.push(JoinedTransitionSeq {
                transitions: first_path.transitions,
            });
            // Link remaining pairs to this new destination
            for (src, keys) in pairs.iter().skip(1) {
                let cost_info = TransitionCostInfo::new(src.outgoing_cost, translation_id);
                let transitions = self.link_chain(src.src_node_index, first_path.dst_node_id, keys, &cost_info);
                transition_seqs.push(JoinedTransitionSeq { transitions });
            }
            return JoinedTriePaths {
                dst_node_id: Some(first_path.dst_node_id),
                transition_seqs,
            };
        };

        // dst_node_id is Some, link all pairs to it
        for (src, keys) in pairs {
            let cost_info = TransitionCostInfo::new(src.outgoing_cost, translation_id);
            let transitions = self.link_chain(src.src_node_index, actual_dst_node_id, keys, &cost_info);
            transition_seqs.push(JoinedTransitionSeq { transitions });
        }

        JoinedTriePaths {
            dst_node_id: Some(actual_dst_node_id),
            transition_seqs,
        }
    }

    /// Sets a translation at a node.
    pub fn set_translation(&mut self, node_id: usize, translation_id: usize) {
        self.node_translations
            .entry(node_id)
            .or_insert_with(Vec::new)
            .push(translation_id);
    }

    /// Traverses the trie from source paths following a key.
    pub fn traverse<'a>(
        &'a self,
        src_node_paths: impl Iterator<Item = TriePath> + 'a,
        key_id: Option<usize>,
    ) -> impl Iterator<Item = TriePath> + 'a {
        src_node_paths.flat_map(move |path| {
            let transitions = &self.transitions[path.dst_node_id];
            
            transitions.get(&key_id).into_iter().flat_map(move |dst_node_ids| {
                dst_node_ids.iter().enumerate().flat_map({
                    let path = path.clone();
                    move |(transition_index, &dst_node_id)| {
                        let transition_key = TransitionKey::new(path.dst_node_id, key_id, transition_index);
                        let mut new_transitions = path.transitions.clone();
                        new_transitions.push(transition_key);
                        
                        self.dfs_empty_transitions(
                            TriePath::new(dst_node_id, new_transitions),
                            HashSet::new(),
                        )
                    }
                })
            })
        })
    }

    /// DFS to follow empty (None key) transitions.
    fn dfs_empty_transitions(
        &self,
        src_node_path: TriePath,
        visited_transitions: HashSet<TransitionKey>,
    ) -> Vec<TriePath> {
        let mut results = vec![src_node_path.clone()];

        let transitions = &self.transitions[src_node_path.dst_node_id];
        if let Some(dst_node_ids) = transitions.get(&None) {
            for (transition_index, &dst_node_id) in dst_node_ids.iter().enumerate() {
                let transition_key = TransitionKey::new(src_node_path.dst_node_id, None, transition_index);
                
                if visited_transitions.contains(&transition_key) {
                    continue;
                }

                let mut new_transitions = src_node_path.transitions.clone();
                new_transitions.push(transition_key);
                
                let mut new_visited = visited_transitions.clone();
                new_visited.insert(transition_key);

                results.extend(self.dfs_empty_transitions(
                    TriePath::new(dst_node_id, new_transitions),
                    new_visited,
                ));
            }
        }

        results
    }

    /// Traverses the trie following a chain of keys.
    pub fn traverse_chain<'a>(
        &'a self,
        src_node_paths: impl Iterator<Item = TriePath> + 'a,
        key_ids: &'a [Option<usize>],
    ) -> Box<dyn Iterator<Item = TriePath> + 'a> {
        let mut current: Box<dyn Iterator<Item = TriePath> + 'a> = Box::new(src_node_paths);
        for &key_id in key_ids {
            current = Box::new(self.traverse(current, key_id));
        }
        current
    }

    /// Gets translations and costs for a single node.
    pub fn get_translations_and_costs_single(
        &self,
        node_id: usize,
        transitions: &[TransitionKey],
    ) -> Vec<(usize, f64)> {
        let Some(translation_ids) = self.node_translations.get(&node_id) else {
            return Vec::new();
        };

        let mut results = Vec::new();

        for &translation_id in translation_ids {
            let mut is_valid_path = true;
            let mut cumsum_cost = 0.0;

            for transition in transitions {
                let key = TransitionCostKey::new(*transition, translation_id);
                if let Some(&cost) = self.transition_costs.get(&key) {
                    cumsum_cost += cost;
                } else {
                    is_valid_path = false;
                    break;
                }
            }

            if is_valid_path {
                results.push((translation_id, cumsum_cost));
            }
        }

        results
    }

    /// Gets translations and costs for multiple paths.
    pub fn get_translations_and_costs<'a>(
        &'a self,
        node_paths: impl Iterator<Item = TriePath> + 'a,
    ) -> impl Iterator<Item = LookupResult> + 'a {
        node_paths.flat_map(move |path| {
            self.get_translations_and_costs_single(path.dst_node_id, &path.transitions)
                .into_iter()
                .map(move |(translation_id, cost)| {
                    LookupResult::new(translation_id, cost, path.transitions.clone())
                })
        })
    }

    /// Gets the cost of a specific transition for a translation.
    pub fn get_transition_cost(
        &self,
        transition: &TransitionKey,
        translation_id: usize,
    ) -> Option<f64> {
        let cost_key = TransitionCostKey::new(*transition, translation_id);
        self.transition_costs.get(&cost_key).copied()
    }

    /// Checks if a transition has a specific key.
    pub fn transition_has_key(&self, transition: &TransitionKey, key_id: Option<usize>) -> bool {
        transition.key_id == key_id
    }

    /// Gets translations with minimum costs for each translation_id.
    pub fn get_translations_and_min_costs(
        &self,
        node_paths: impl Iterator<Item = TriePath>,
    ) -> Vec<LookupResult> {
        let mut min_cost_results: HashMap<usize, LookupResult> = HashMap::new();

        for path in node_paths {
            for (translation_id, cost) in
                self.get_translations_and_costs_single(path.dst_node_id, &path.transitions)
            {
                let should_update = match min_cost_results.get(&translation_id) {
                    None => true,
                    Some(existing) => cost < existing.cost,
                };

                if should_update {
                    min_cost_results.insert(
                        translation_id,
                        LookupResult::new(translation_id, cost, path.transitions.clone()),
                    );
                }
            }
        }

        min_cost_results.into_values().collect()
    }

    /// Gets translations associated with a node.
    pub fn get_node_translations(&self, node_id: usize) -> Option<&Vec<usize>> {
        self.node_translations.get(&node_id)
    }

    /// Gets all transitions from a node.
    pub fn get_transitions_from_node(&self, node_id: usize) -> Option<&HashMap<Option<usize>, Vec<usize>>> {
        self.transitions.get(node_id)
    }

    /// Gets the number of nodes in the trie.
    pub fn n_nodes(&self) -> usize {
        self.transitions.len()
    }

    /// Gets all translation IDs that have been set.
    pub fn get_all_translation_ids(&self) -> Vec<usize> {
        let mut ids: HashSet<usize> = HashSet::new();
        for translation_ids in self.node_translations.values() {
            for &id in translation_ids {
                ids.insert(id);
            }
        }
        ids.into_iter().collect()
    }

    /// Builds a reverse mapping from destination nodes to source nodes.
    pub fn reversed_nodes(&self) -> ReverseNodes {
        let mut reverse_nodes: ReverseNodes = HashMap::new();

        for (src_node_id, transitions) in self.transitions.iter().enumerate() {
            for (&key_id, dst_node_ids) in transitions.iter() {
                for (transition_index, &dst_node_id) in dst_node_ids.iter().enumerate() {
                    reverse_nodes
                        .entry(dst_node_id)
                        .or_insert_with(HashMap::new)
                        .entry(key_id)
                        .or_insert_with(Vec::new)
                        .push((src_node_id, transition_index));
                }
            }
        }

        reverse_nodes
    }

    /// Builds a reverse mapping from translation IDs to nodes.
    pub fn reversed_translations(&self) -> ReverseTranslations {
        let mut reverse_translations: ReverseTranslations = HashMap::new();

        for (&node_id, translation_ids) in self.node_translations.iter() {
            for &translation_id in translation_ids {
                reverse_translations
                    .entry(translation_id)
                    .or_insert_with(Vec::new)
                    .push(node_id);
            }
        }

        reverse_translations
    }

    pub fn get_reverse_lookup_results(
        &self,
        reverse_nodes: &ReverseNodes,
        reverse_translations: &ReverseTranslations,
        translation_id: usize,
    ) -> Vec<LookupResult> {
        let mut results = Vec::new();
        if let Some(nodes) = reverse_translations.get(&translation_id) {
            for &node in nodes {
                let mut visited_nodes = HashSet::new();
                visited_nodes.insert(node);
                self.dfs_reverse_lookup(
                    node,
                    translation_id,
                    &mut Vec::new(),
                    0.0,
                    &mut visited_nodes,
                    reverse_nodes,
                    &mut results,
                );
            }
        }
        results
    }

    fn dfs_reverse_lookup(
        &self,
        node: usize,
        translation_id: usize,
        transitions_reversed: &mut Vec<TransitionKey>,
        cost: f64,
        visited_nodes: &mut HashSet<usize>,
        reverse_nodes: &ReverseNodes,
        results: &mut Vec<LookupResult>,
    ) {
        if node == Self::ROOT {
            let mut final_transitions = transitions_reversed.clone();
            final_transitions.reverse();
            results.push(LookupResult::new(translation_id, cost, final_transitions));
            return;
        }

        if let Some(src_nodes_map) = reverse_nodes.get(&node) {
            for (&key_id, src_nodes) in src_nodes_map {
                for &(src_node_id, transition_index) in src_nodes {
                    if visited_nodes.contains(&src_node_id) {
                        continue;
                    }

                    if !self.transition_has_cost_for_translation(
                        src_node_id,
                        key_id,
                        transition_index,
                        translation_id,
                    ) {
                        continue;
                    }

                    let transition_key = TransitionKey::new(src_node_id, key_id, transition_index);
                    let cost_key = TransitionCostKey::new(transition_key, translation_id);
                    let transition_cost = *self.transition_costs.get(&cost_key).unwrap_or(&0.0);

                    transitions_reversed.push(transition_key);
                    visited_nodes.insert(src_node_id);

                    self.dfs_reverse_lookup(
                        src_node_id,
                        translation_id,
                        transitions_reversed,
                        cost + transition_cost,
                        visited_nodes,
                        reverse_nodes,
                        results,
                    );

                    visited_nodes.remove(&src_node_id);
                    transitions_reversed.pop();
                }
            }
        }
    }

    pub fn get_subtrie_data(
        &self,
        reverse_nodes: &ReverseNodes,
        reverse_translations: &ReverseTranslations,
        translation_id: usize,
    ) -> Option<SubtrieData> {
        if !reverse_translations.contains_key(&translation_id) {
            return None;
        }

        let mut visited_nodes = HashSet::new();
        let mut nodes_toposort = Vec::new();
        // (src, dst) -> list of key, transition_index
        let mut visited_transitions: HashMap<(usize, usize), Vec<(Option<usize>, usize)>> =
            HashMap::new();

        if let Some(nodes) = reverse_translations.get(&translation_id) {
            for &node in nodes {
                self.dfs_subtrie(
                    node,
                    translation_id,
                    &mut visited_nodes,
                    reverse_nodes,
                    &mut visited_transitions,
                    &mut nodes_toposort,
                );
            }
        }

        let mut transitions = Vec::new();
        for ((src_node_id, dst_node_id), key_indices) in visited_transitions {
            let mut key_infos = Vec::new();
            for (key_id, transition_index) in key_indices {
                let cost_key = TransitionCostKey::new(
                    TransitionKey::new(src_node_id, key_id, transition_index),
                    translation_id,
                );
                let cost = *self.transition_costs.get(&cost_key).unwrap_or(&0.0);
                key_infos.push((key_id, transition_index, cost));
            }
            transitions.push(SubtrieTransition {
                src_node_id,
                dst_node_id,
                key_infos,
            });
        }

        Some(SubtrieData {
            nodes: nodes_toposort,
            transitions,
            translation_nodes: reverse_translations.get(&translation_id).cloned().unwrap_or_default(),
        })
    }

    fn dfs_subtrie(
        &self,
        node: usize,
        translation_id: usize,
        visited_nodes: &mut HashSet<usize>,
        reverse_nodes: &ReverseNodes,
        visited_transitions: &mut HashMap<(usize, usize), Vec<(Option<usize>, usize)>>,
        nodes_toposort: &mut Vec<usize>,
    ) {
        if visited_nodes.contains(&node) {
            return;
        }
        visited_nodes.insert(node);

        if let Some(src_nodes_map) = reverse_nodes.get(&node) {
            for (&key_id, src_nodes) in src_nodes_map {
                for &(src_node_id, transition_index) in src_nodes {
                    if !self.transition_has_cost_for_translation(
                        src_node_id,
                        key_id,
                        transition_index,
                        translation_id,
                    ) {
                        continue;
                    }

                    self.dfs_subtrie(
                        src_node_id,
                        translation_id,
                        visited_nodes,
                        reverse_nodes,
                        visited_transitions,
                        nodes_toposort,
                    );

                    visited_transitions
                        .entry((src_node_id, node))
                        .or_insert_with(Vec::new)
                        .push((key_id, transition_index));
                }
            }
        }

        nodes_toposort.push(node);
    }

    /// Checks if a transition has a cost for a specific translation.
    pub fn transition_has_cost_for_translation(
        &self,
        src_node_id: usize,
        key_id: Option<usize>,
        transition_index: usize,
        translation_id: usize,
    ) -> bool {
        let cost_key = TransitionCostKey::new(
            TransitionKey::new(src_node_id, key_id, transition_index),
            translation_id,
        );
        self.transition_costs.contains_key(&cost_key)
    }
}

impl Default for NondeterministicTrie {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_trie() {
        let trie = NondeterministicTrie::new();
        assert_eq!(trie.transitions.len(), 1);
    }

    #[test]
    fn test_follow_creates_node() {
        let mut trie = NondeterministicTrie::new();
        let cost_info = TransitionCostInfo::new(1.0, 0);
        let path = trie.follow(0, Some(1), &cost_info);
        assert_eq!(path.dst_node_id, 1);
        assert_eq!(path.transitions.len(), 1);
    }

    #[test]
    fn test_set_and_get_translation() {
        let mut trie = NondeterministicTrie::new();
        let cost_info = TransitionCostInfo::new(1.0, 0);
        let path = trie.follow(0, Some(1), &cost_info);
        trie.set_translation(path.dst_node_id, 42);
        
        let results: Vec<_> = trie.get_translations_and_costs_single(path.dst_node_id, &path.transitions);
        assert_eq!(results.len(), 1);
        assert_eq!(results[0], (42, 1.0));
    }
}