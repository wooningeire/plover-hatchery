use std::{
    collections::HashMap,
    hash::{DefaultHasher, Hash, Hasher},
};

use pyo3::{prelude::*, types::PyTuple};

use crate::{pipes::TheorySymbol, py_stroke::stroke_from_integer, trie::TriePath};

const ROOT_NODE_ID: usize = 0;

/// Active position in a chord-to-theory-symbol trie lookup.
#[derive(Clone, Debug)]
#[pyclass]
#[pyo3(name = "ChordToTheorySymbolSearchNode")]
pub struct PyChordToTheorySymbolSearchNode {
    #[pyo3(get)]
    pub trie_node_id: usize,
    #[pyo3(get)]
    pub chord_starting_key_index: usize,
}

#[pymethods]
impl PyChordToTheorySymbolSearchNode {
    #[new]
    pub fn new(trie_node_id: usize, chord_starting_key_index: usize) -> Self {
        Self {
            trie_node_id,
            chord_starting_key_index,
        }
    }
}

/// Candidate theory-symbol sequence found after matching a chord.
#[derive(Clone, Debug)]
#[pyclass]
#[pyo3(name = "ChordToTheorySymbolSearchResult")]
pub struct PyChordToTheorySymbolSearchResult {
    theory_symbols: Vec<TheorySymbol>,
    chord: usize,
}

#[pymethods]
impl PyChordToTheorySymbolSearchResult {
    #[new]
    pub fn new(theory_symbols: Vec<TheorySymbol>, chord: Py<PyAny>, py: Python<'_>) -> PyResult<Self> {
        Ok(Self {
            theory_symbols,
            chord: chord.extract(py)?,
        })
    }

    #[getter]
    pub fn theory_symbols<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        PyTuple::new(py, self.theory_symbols.clone())
    }

    #[getter]
    pub fn chord(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        Ok(stroke_from_integer(py, self.chord)?.unbind())
    }

    pub fn __hash__(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.theory_symbols.hash(&mut hasher);
        self.chord.hash(&mut hasher);
        hasher.finish()
    }

    pub fn __eq__(&self, other: &PyChordToTheorySymbolSearchResult) -> bool {
        self.theory_symbols == other.theory_symbols && self.chord == other.chord
    }
}

/// A path through the theory-symbol trie during lookup, including unresolved chord associations.
#[pyclass]
#[pyo3(name = "TheorySymbolsToTranslationSearchPath")]
pub struct PyTheorySymbolsToTranslationSearchPath {
    trie_path: TriePath,
    theory_symbols_and_chords_used: Py<PyAny>,
}

#[pymethods]
impl PyTheorySymbolsToTranslationSearchPath {
    #[new]
    #[pyo3(signature = (trie_path=None, theory_symbols_and_chords_used=None))]
    pub fn new(
        trie_path: Option<TriePath>,
        theory_symbols_and_chords_used: Option<Py<PyAny>>,
        py: Python<'_>,
    ) -> Self {
        Self {
            trie_path: trie_path.unwrap_or_else(TriePath::root),
            theory_symbols_and_chords_used: theory_symbols_and_chords_used
                .unwrap_or_else(|| PyTuple::empty(py).unbind().into_any()),
        }
    }

    #[getter]
    pub fn trie_path(&self) -> TriePath {
        self.trie_path.clone()
    }

    #[getter]
    pub fn theory_symbols_and_chords_used(&self, py: Python<'_>) -> Py<PyAny> {
        self.theory_symbols_and_chords_used.clone_ref(py)
    }
}

/// TheorySymbol result emitted by a chord lookup, paired with the key index where that chord began.
#[pyclass]
#[pyo3(name = "ChordToTheorySymbolSearchMatch")]
pub struct PyChordToTheorySymbolSearchMatch {
    theory_symbol_result: Py<PyChordToTheorySymbolSearchResult>,
    #[pyo3(get)]
    pub chord_starting_key_index: usize,
}

#[pymethods]
impl PyChordToTheorySymbolSearchMatch {
    #[new]
    pub fn new(
        theory_symbol_result: Py<PyChordToTheorySymbolSearchResult>,
        chord_starting_key_index: usize,
    ) -> Self {
        Self {
            theory_symbol_result,
            chord_starting_key_index,
        }
    }

    #[getter]
    pub fn theory_symbol_result(&self, py: Python<'_>) -> Py<PyChordToTheorySymbolSearchResult> {
        self.theory_symbol_result.clone_ref(py)
    }
}

/// Rust-owned trie for matching physical chord keys to Python theory-symbol search results.
///
/// The searcher keeps `ChordToTheorySymbolSearchResult` values and returns matches paired with the key index where each chord began.
#[pyclass]
#[pyo3(name = "ChordToTheorySymbolSearcher")]
pub struct PyChordToTheorySymbolSearcher {
    transitions: Vec<HashMap<String, usize>>,
    node_results: HashMap<usize, Vec<Py<PyChordToTheorySymbolSearchResult>>>,
}

#[pymethods]
impl PyChordToTheorySymbolSearcher {
    #[new]
    pub fn new(entries: Vec<(Vec<String>, Py<PyChordToTheorySymbolSearchResult>)>) -> Self {
        let mut searcher = Self {
            transitions: vec![HashMap::new()],
            node_results: HashMap::new(),
        };

        for (keys, result) in entries {
            let node_id = searcher.follow_chain(&keys);
            searcher
                .node_results
                .entry(node_id)
                .or_default()
                .push(result);
        }

        searcher
    }

    /// Advance every in-progress chord lookup by one key.
    ///
    /// The caller passes active trie nodes paired with the key index where each chord
    /// began. This also starts a fresh traversal at the root for the current key, so
    /// chords can begin at any key position within a stroke.
    pub fn possible_theory_symbols_after_consuming(
        &self,
        node_data: Vec<PyRef<PyChordToTheorySymbolSearchNode>>,
        current_key_index: usize,
        key: String,
        py: Python<'_>,
    ) -> (Vec<PyChordToTheorySymbolSearchNode>, Vec<PyChordToTheorySymbolSearchMatch>) {
        // Add a root node to trigger a new traversal starting from the root.
        let mut src_nodes: Vec<PyChordToTheorySymbolSearchNode> =
            node_data.iter().map(|node| (*node).clone()).collect();
        src_nodes.push(PyChordToTheorySymbolSearchNode::new(
            ROOT_NODE_ID,
            current_key_index,
        ));

        let mut new_node_data = Vec::new();
        let mut results = Vec::new();

        // Continue the ongoing trie traversals and report every chord that ends here.
        for src_node in src_nodes {
            let Some(dst_node_id) = self
                .transitions
                .get(src_node.trie_node_id)
                .and_then(|transitions| transitions.get(&key))
                .copied()
            else {
                continue;
            };

            new_node_data.push(PyChordToTheorySymbolSearchNode::new(
                dst_node_id,
                src_node.chord_starting_key_index,
            ));

            if let Some(node_results) = self.node_results.get(&dst_node_id) {
                for result in node_results {
                    results.push(PyChordToTheorySymbolSearchMatch::new(
                        result.clone_ref(py),
                        src_node.chord_starting_key_index,
                    ));
                }
            }
        }

        (new_node_data, results)
    }
}

impl PyChordToTheorySymbolSearcher {
    fn create_node(&mut self) -> usize {
        let node_id = self.transitions.len();
        self.transitions.push(HashMap::new());
        node_id
    }

    fn follow_chain(&mut self, keys: &[String]) -> usize {
        let mut node_id = 0;

        for key in keys {
            let maybe_next_node_id = self.transitions[node_id].get(key).copied();
            node_id = match maybe_next_node_id {
                Some(next_node_id) => next_node_id,
                None => {
                    let next_node_id = self.create_node();
                    self.transitions[node_id].insert(key.clone(), next_node_id);
                    next_node_id
                }
            };
        }

        node_id
    }
}
