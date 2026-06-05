use std::collections::HashMap;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use super::binary::{BinaryReader, BinaryWriter};
use super::transition::TransitionCostKey;
use super::transition_flag::TransitionFlag;

pub type ExportedTransitionFlagMappings = Vec<((usize, Option<usize>, usize, usize), Vec<usize>)>;
pub type ExportedTransitionFlagState = (Vec<String>, ExportedTransitionFlagMappings);

const BINARY_STATE_MAGIC: &[u8] = b"PHNFLG2\0";

#[derive(Debug, Clone)]
#[pyclass]
pub struct TransitionFlagManager {
    pub mappings: HashMap<TransitionCostKey, Vec<usize>>,
    pub flag_types: Vec<TransitionFlag>,
}

impl TransitionFlagManager {
    pub fn flag_transition(&mut self, transition_cost_key: TransitionCostKey, flag_index: usize) {
        self.mappings
            .entry(transition_cost_key)
            .or_default()
            .push(flag_index);
    }
}

#[pymethods]
impl TransitionFlagManager {
    #[new]
    pub fn new() -> Self {
        Self {
            mappings: HashMap::new(),
            flag_types: Vec::new(),
        }
    }

    pub fn new_flag(&mut self, label: String) -> usize {
        let flag = TransitionFlag::new(label);
        self.flag_types.push(flag.clone());
        self.flag_types.len() - 1
    }

    #[pyo3(name = "flag_transition")]
    pub fn flag_transition_py(
        &mut self,
        transition_cost_key: Py<TransitionCostKey>,
        flag_index: usize,
        py: Python<'_>,
    ) {
        self.flag_transition(*transition_cost_key.borrow(py), flag_index);
    }

    pub fn get_label(&self, flag_index: usize) -> &str {
        &self.flag_types[flag_index].label
    }

    pub fn get_flags(&self, transition_cost_key: TransitionCostKey) -> Vec<usize> {
        self.mappings
            .get(&transition_cost_key)
            .cloned()
            .unwrap_or_default()
    }

    pub fn export_state(&self) -> ExportedTransitionFlagState {
        let labels = self
            .flag_types
            .iter()
            .map(|flag| flag.label.clone())
            .collect();

        let mappings = self
            .mappings
            .iter()
            .map(|(cost_key, flag_ids)| {
                (
                    (
                        cost_key.transition_key.src_node_index,
                        cost_key.transition_key.key_id,
                        cost_key.transition_key.transition_index,
                        cost_key.translation_id,
                    ),
                    flag_ids.clone(),
                )
            })
            .collect();

        (labels, mappings)
    }

    pub fn export_state_bytes<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        PyBytes::new(py, &self.export_state_bytes_raw())
    }

    #[staticmethod]
    pub fn from_state(labels: Vec<String>, mappings: ExportedTransitionFlagMappings) -> Self {
        Self {
            flag_types: labels.into_iter().map(TransitionFlag::new).collect(),
            mappings: mappings
                .into_iter()
                .map(
                    |((src_node_index, key_id, transition_index, translation_id), flag_ids)| {
                        (
                            TransitionCostKey::new(
                                super::transition::TransitionKey::new(
                                    src_node_index,
                                    key_id,
                                    transition_index,
                                ),
                                translation_id,
                            ),
                            flag_ids,
                        )
                    },
                )
                .collect(),
        }
    }

    pub fn load_state(&mut self, labels: Vec<String>, mappings: ExportedTransitionFlagMappings) {
        *self = Self::from_state(labels, mappings);
    }

    #[staticmethod]
    pub fn from_state_bytes(bytes: &[u8]) -> PyResult<Self> {
        Self::from_state_bytes_raw(bytes).map_err(PyValueError::new_err)
    }

    pub fn load_state_bytes(&mut self, bytes: &[u8]) -> PyResult<()> {
        *self = Self::from_state_bytes_raw(bytes).map_err(PyValueError::new_err)?;
        Ok(())
    }
}

impl TransitionFlagManager {
    fn export_state_bytes_raw(&self) -> Vec<u8> {
        let mut writer = BinaryWriter::new();
        writer.write_magic(BINARY_STATE_MAGIC);

        writer.write_usize(self.flag_types.len());
        for flag in &self.flag_types {
            writer.write_string(&flag.label);
        }

        writer.write_usize(self.mappings.len());
        for (cost_key, flag_ids) in &self.mappings {
            writer.write_usize(cost_key.transition_key.src_node_index);
            writer.write_option_usize(cost_key.transition_key.key_id);
            writer.write_usize(cost_key.transition_key.transition_index);
            writer.write_usize(cost_key.translation_id);
            writer.write_usize_slice(flag_ids);
        }

        writer.into_bytes()
    }

    fn from_state_bytes_raw(bytes: &[u8]) -> Result<Self, String> {
        let mut reader = BinaryReader::new(bytes);
        reader.read_magic(BINARY_STATE_MAGIC)?;

        let flag_count = reader.read_usize()?;
        let mut flag_types = Vec::with_capacity(flag_count);
        for _ in 0..flag_count {
            flag_types.push(TransitionFlag::new(reader.read_string()?));
        }

        let mapping_count = reader.read_usize()?;
        let mut mappings = HashMap::with_capacity(mapping_count);
        for _ in 0..mapping_count {
            let src_node_index = reader.read_usize()?;
            let key_id = reader.read_option_usize()?;
            let transition_index = reader.read_usize()?;
            let translation_id = reader.read_usize()?;
            let flag_ids = reader.read_usize_vec()?;
            mappings.insert(
                TransitionCostKey::new(
                    super::transition::TransitionKey::new(src_node_index, key_id, transition_index),
                    translation_id,
                ),
                flag_ids,
            );
        }

        reader.finish()?;
        Ok(Self {
            mappings,
            flag_types,
        })
    }
}
