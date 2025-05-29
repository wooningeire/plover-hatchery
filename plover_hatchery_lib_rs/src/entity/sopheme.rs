use pyo3::{prelude::*};


#[pyclass]
pub struct Sopheme {
    chars: String,
    keysymbols: Vec<PyObject>,
}

#[pymethods]
impl Sopheme {
    #[new]
    pub fn new(chars: String, keysymbols: Vec<PyObject>) -> Self {
        Sopheme {
            chars,
            keysymbols,
        }
    }

    #[getter]
    pub fn can_be_silent(&self, py: Python<'_>) -> bool {
        self.keysymbols.iter()
            .all(|keysymbol| keysymbol.getattr(py, "optional").expect("").extract::<bool>(py).expect(""))
    }

    pub fn __str__(&self, py: Python<'_>) -> String {
        let mut keysymbols_string = self.keysymbols.iter()
            .map(|keysymbol| keysymbol.call_method0(py, "__str__").expect("").extract::<String>(py).expect(""))
            .collect::<Vec<_>>()
            .join(" ");

        if self.keysymbols.len() > 1 {
            keysymbols_string = format!("({keysymbols_string})");
        }

        format!("{chars}.{keysymbols_string}", chars=self.chars)
    }

    pub fn __repr__(&self, py: Python<'_>) -> String {
        self.__str__(py)
    }
}


/*
@dataclass(frozen=True)
class Sopheme:
    chars: str
    keysymbols: tuple[Keysymbol, ...]

    @property
    def can_be_silent(self):
        return all(keysymbol.optional for keysymbol in self.keysymbols)

    def __str__(self):
        keysymbols_string = " ".join(str(keysymbol) for keysymbol in self.keysymbols)
        if len(self.keysymbols) > 1:
            keysymbols_string = f"({keysymbols_string})"

        return f"{self.chars}.{keysymbols_string}"
    
    __repr__ = __str__

    @staticmethod
    def format_seq(sophemes: "Iterable[Sopheme]"):
        return " ".join(str(sopheme) for sopheme in sophemes)

    @staticmethod
    def get_translation(sophemes: "Iterable[Sopheme]"):
        return "".join(sopheme.chars for sopheme in sophemes)
        
 */