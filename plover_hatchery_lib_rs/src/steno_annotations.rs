use std::hash::{DefaultHasher, Hash, Hasher};

use pyo3::{prelude::*, types::PyTuple};

use crate::py_stroke::stroke_from_integer;

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
#[pyclass]
pub struct AsteriskableKey {
    #[pyo3(get)]
    key: String,
    #[pyo3(get)]
    asterisk: bool,
}

#[pymethods]
impl AsteriskableKey {
    #[new]
    pub fn new(key: String, asterisk: bool) -> Self {
        Self { key, asterisk }
    }

    #[staticmethod]
    pub fn annotations_from_outline<'py>(
        outline_steno: &str,
        py: Python<'py>,
    ) -> PyResult<Bound<'py, PyTuple>> {
        let stroke_class = py.import("plover.steno")?.getattr("Stroke")?;
        let strokes = outline_steno
            .split('/')
            .map(|steno| stroke_class.call_method1("from_steno", (steno,)))
            .collect::<PyResult<Vec<Bound<'py, PyAny>>>>()?;

        Self::annotations_from_stroke_objects(strokes.into_iter(), py)
    }

    #[staticmethod]
    pub fn annotations_from_strokes<'py>(
        strokes: &Bound<'py, PyAny>,
        py: Python<'py>,
    ) -> PyResult<Bound<'py, PyTuple>> {
        let strokes = strokes.try_iter()?.collect::<PyResult<Vec<_>>>()?;
        Self::annotations_from_stroke_objects(strokes.into_iter(), py)
    }

    pub fn __str__(&self) -> String {
        self.to_string()
    }

    pub fn __repr__(&self) -> String {
        self.to_string()
    }

    pub fn __hash__(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.hash(&mut hasher);
        hasher.finish()
    }

    pub fn __eq__(&self, other: &AsteriskableKey) -> bool {
        self == other
    }
}

impl AsteriskableKey {
    fn annotations_from_stroke_objects<'py>(
        strokes: impl Iterator<Item = Bound<'py, PyAny>>,
        py: Python<'py>,
    ) -> PyResult<Bound<'py, PyTuple>> {
        let asterisk_stroke = py
            .import("plover.steno")?
            .getattr("Stroke")?
            .call_method1("from_steno", ("*",))?;
        let asterisk_integer = asterisk_stroke.extract::<usize>()?;

        let mut annotations = Vec::new();
        for stroke in strokes {
            let stroke_integer = stroke.extract::<usize>()?;
            let has_asterisk = stroke_integer & asterisk_integer != 0;
            let stroke_without_asterisk =
                stroke_from_integer(py, stroke_integer & !asterisk_integer)?;
            let keys = stroke_without_asterisk
                .call_method0("keys")?
                .extract::<Vec<String>>()?;

            annotations.extend(
                keys.into_iter()
                    .map(|key| AsteriskableKey::new(key, has_asterisk)),
            );
        }

        PyTuple::new(py, annotations)
    }

    fn to_string(&self) -> String {
        format!("{}{}", self.key, if self.asterisk { "(*)" } else { "" })
    }
}
