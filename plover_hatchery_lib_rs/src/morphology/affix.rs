use pyo3::prelude::*;


#[pyclass(get_all)]
pub struct AffixKey {
    pub is_suffix: bool,
    pub name: String,
    pub phono: String,
    pub ortho: String,
}

#[pymethods]
impl AffixKey {
    #[new]
    pub fn new(is_suffix: bool, name: String, phono: String, ortho: String) -> AffixKey {
        AffixKey {
            is_suffix,
            name,
            phono,
            ortho,
        }
    }
}