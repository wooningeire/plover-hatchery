use pyo3::prelude::*;

pub fn stroke_from_integer<'py>(
    py: Python<'py>,
    stroke_integer: usize,
) -> PyResult<Bound<'py, PyAny>> {
    py.import("plover.steno")?
        .getattr("Stroke")?
        .call_method1("from_integer", (stroke_integer,))
}
