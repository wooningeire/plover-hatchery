use std::collections::HashMap;

use pyo3::{exceptions::PyIndexError, prelude::*, types::PyDict};

const ROOT_NODE_ID: usize = 0;

/// Deterministic trie that keeps arbitrary Python keys and translations opaque.
#[pyclass]
#[pyo3(name = "Trie")]
pub struct PyTrie {
    nodes: Vec<Vec<(usize, usize)>>,
    translations: Py<PyDict>,
    keys: Py<PyDict>,
}

#[pymethods]
impl PyTrie {
    #[new]
    pub fn new(py: Python<'_>) -> Self {
        Self {
            nodes: vec![Vec::new()],
            translations: PyDict::new(py).unbind(),
            keys: PyDict::new(py).unbind(),
        }
    }

    pub fn follow(&mut self, src_node: usize, key: Py<PyAny>, py: Python<'_>) -> PyResult<usize> {
        self.follow_key(py, src_node, key.bind(py))
    }

    pub fn follow_chain(
        &mut self,
        src_node: usize,
        keys: Vec<Py<PyAny>>,
        py: Python<'_>,
    ) -> PyResult<usize> {
        let mut current_node = src_node;

        for key in keys {
            current_node = self.follow_key(py, current_node, key.bind(py))?;
        }

        Ok(current_node)
    }

    pub fn traverse(
        &self,
        src_node: usize,
        key: Py<PyAny>,
        py: Python<'_>,
    ) -> PyResult<Option<usize>> {
        self.traverse_key(py, src_node, key.bind(py))
    }

    pub fn traverse_chain(
        &self,
        src_node: usize,
        keys: Vec<Py<PyAny>>,
        py: Python<'_>,
    ) -> PyResult<Option<usize>> {
        let mut current_node = src_node;

        for key in keys {
            let Some(next_node) = self.traverse_key(py, current_node, key.bind(py))? else {
                return Ok(None);
            };

            current_node = next_node;
        }

        Ok(Some(current_node))
    }

    pub fn set_translation(
        &mut self,
        node: usize,
        translation: Py<PyAny>,
        py: Python<'_>,
    ) -> PyResult<()> {
        self.translations.bind(py).set_item(node, translation)
    }

    pub fn get_translation(&self, node: usize, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        self.translations
            .bind(py)
            .get_item(node)?
            .map(|translation| Ok(translation.unbind()))
            .transpose()
    }

    pub fn node_has_translations(&self, node: usize, py: Python<'_>) -> PyResult<bool> {
        self.translations.bind(py).contains(node)
    }

    pub fn frozen(&self, py: Python<'_>) -> PyReadonlyTrie {
        let nodes = self
            .nodes
            .iter()
            .enumerate()
            .flat_map(|(src_node, transitions)| {
                transitions
                    .iter()
                    .map(move |(key_id, dst_node)| ((src_node, *key_id), *dst_node))
            })
            .collect();

        PyReadonlyTrie {
            nodes,
            translations: self.translations.clone_ref(py),
            keys: self.keys.clone_ref(py),
        }
    }

    pub fn __str__(&self, py: Python<'_>) -> PyResult<String> {
        let mut lines: Vec<String> = Vec::new();
        let key_ids_to_keys = self.key_ids_to_keys(py)?;
        let translations = self.translations.bind(py);

        for (node, transitions) in self.nodes.iter().enumerate() {
            if let Some(translation) = translations.get_item(node)? {
                lines.push(format!("{} : {}", node, translation.str()?.to_str()?));
            } else {
                lines.push(node.to_string());
            }

            for (key_id, dst_node) in transitions {
                let Some(key) = key_ids_to_keys.get(key_id) else {
                    continue;
                };

                lines.push(format!(
                    "\t{}\t ->\t {}",
                    key.bind(py).str()?.to_str()?,
                    dst_node
                ));
            }
        }

        Ok(lines.join("\n"))
    }

    #[classattr]
    const ROOT: usize = ROOT_NODE_ID;
}

impl PyTrie {
    fn follow_key(
        &mut self,
        py: Python<'_>,
        src_node: usize,
        key: &Bound<'_, PyAny>,
    ) -> PyResult<usize> {
        let key_id = self.get_key_id_else_create(py, key)?;

        if let Some(dst_node) = self.find_transition(src_node, key_id)? {
            return Ok(dst_node);
        }

        let new_node_id = self.nodes.len();
        self.transitions_for_node_mut(src_node)?
            .push((key_id, new_node_id));
        self.nodes.push(Vec::new());

        Ok(new_node_id)
    }

    fn traverse_key(
        &self,
        py: Python<'_>,
        src_node: usize,
        key: &Bound<'_, PyAny>,
    ) -> PyResult<Option<usize>> {
        let Some(key_id) = self.get_existing_key_id(py, key)? else {
            return Ok(None);
        };

        self.find_transition(src_node, key_id)
    }

    fn get_key_id_else_create(&self, py: Python<'_>, key: &Bound<'_, PyAny>) -> PyResult<usize> {
        if let Some(key_id) = self.get_existing_key_id(py, key)? {
            return Ok(key_id);
        }

        let keys = self.keys.bind(py);
        let new_key_id = keys.len();
        keys.set_item(key, new_key_id)?;

        Ok(new_key_id)
    }

    fn get_existing_key_id(
        &self,
        py: Python<'_>,
        key: &Bound<'_, PyAny>,
    ) -> PyResult<Option<usize>> {
        self.keys
            .bind(py)
            .get_item(key)?
            .map(|key_id| key_id.extract())
            .transpose()
    }

    fn find_transition(&self, src_node: usize, key_id: usize) -> PyResult<Option<usize>> {
        Ok(self
            .transitions_for_node(src_node)?
            .iter()
            .find_map(|(transition_key_id, dst_node)| {
                (*transition_key_id == key_id).then_some(*dst_node)
            }))
    }

    fn transitions_for_node(&self, src_node: usize) -> PyResult<&Vec<(usize, usize)>> {
        self.nodes
            .get(src_node)
            .ok_or_else(|| PyIndexError::new_err("trie node does not exist"))
    }

    fn transitions_for_node_mut(&mut self, src_node: usize) -> PyResult<&mut Vec<(usize, usize)>> {
        self.nodes
            .get_mut(src_node)
            .ok_or_else(|| PyIndexError::new_err("trie node does not exist"))
    }

    fn key_ids_to_keys(&self, py: Python<'_>) -> PyResult<HashMap<usize, Py<PyAny>>> {
        let mut key_ids_to_keys = HashMap::new();

        for (key, key_id) in self.keys.bind(py).iter() {
            key_ids_to_keys.insert(key_id.extract()?, key.unbind());
        }

        Ok(key_ids_to_keys)
    }
}

#[pyclass]
#[pyo3(name = "ReadonlyTrie")]
pub struct PyReadonlyTrie {
    nodes: HashMap<(usize, usize), usize>,
    translations: Py<PyDict>,
    keys: Py<PyDict>,
}

#[pymethods]
impl PyReadonlyTrie {
    pub fn traverse(
        &self,
        src_node: usize,
        key: Py<PyAny>,
        py: Python<'_>,
    ) -> PyResult<Option<usize>> {
        let Some(key_id) = self.get_existing_key_id(py, key.bind(py))? else {
            return Ok(None);
        };

        Ok(self.nodes.get(&(src_node, key_id)).copied())
    }

    pub fn traverse_chain(
        &self,
        src_node: usize,
        keys: Vec<Py<PyAny>>,
        py: Python<'_>,
    ) -> PyResult<Option<usize>> {
        let mut current_node = src_node;

        for key in keys {
            let Some(next_node) = self.traverse(current_node, key, py)? else {
                return Ok(None);
            };

            current_node = next_node;
        }

        Ok(Some(current_node))
    }

    pub fn get_translation(&self, node: usize, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        self.translations
            .bind(py)
            .get_item(node)?
            .map(|translation| Ok(translation.unbind()))
            .transpose()
    }

    pub fn node_has_translations(&self, node: usize, py: Python<'_>) -> PyResult<bool> {
        self.translations.bind(py).contains(node)
    }

    #[classattr]
    const ROOT: usize = ROOT_NODE_ID;
}

impl PyReadonlyTrie {
    fn get_existing_key_id(
        &self,
        py: Python<'_>,
        key: &Bound<'_, PyAny>,
    ) -> PyResult<Option<usize>> {
        self.keys
            .bind(py)
            .get_item(key)?
            .map(|key_id| key_id.extract())
            .transpose()
    }
}
