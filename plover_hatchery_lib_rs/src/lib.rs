use pyo3::{prelude::*, wrap_pyfunction};

mod py_stroke;

mod steno_annotations;
use steno_annotations::AsteriskableKey;

mod defs;
use defs::{
    py::{
        py_parse_entry_definition, py_parse_keysymbol_seq, py_parse_sopheme_seq, PyDefDict,
        PyDefView, PyDefViewCursor, PyDefViewItem,
    },
    Def, Entity, Keysymbol, Sopheme, SophemeSeq, Transclusion,
};

mod pipes;
use pipes::{
    add_diphthong_keysymbols, add_soph_trie_entry, optionalize_keysymbols,
    PyChordToSophSearchMatch, PyChordToSophSearchNode, PyChordToSophSearchResult,
    PyChordToSophSearcher, PySophsToTranslationSearchPath, Soph,
};

mod morphology;
use morphology::AffixKey;

mod trie;
use trie::{
    py::{PyNondeterministicTrie, PyReverseTrieIndex},
    JoinedTransitionSeq, JoinedTriePaths, LookupResult, PyReadonlyTrie, PyTrie, TransitionCostInfo,
    TransitionCostKey, TransitionFlag, TransitionFlagManager, TransitionKey, TransitionSourceNode,
    TriePath,
};

#[pymodule]
pub fn plover_hatchery_lib_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AsteriskableKey>()?;

    m.add_class::<Def>()?;
    m.add_class::<PyDefDict>()?;
    m.add_class::<PyDefView>()?;
    m.add_class::<PyDefViewCursor>()?;
    m.add_class::<PyDefViewItem>()?;
    m.add_class::<SophemeSeq>()?;
    m.add_class::<Entity>()?;
    m.add_class::<Sopheme>()?;
    m.add_class::<Keysymbol>()?;
    m.add_class::<Transclusion>()?;

    m.add_function(wrap_pyfunction!(optionalize_keysymbols, m)?)?;
    m.add_function(wrap_pyfunction!(add_diphthong_keysymbols, m)?)?;

    m.add_class::<AffixKey>()?;

    m.add_function(wrap_pyfunction!(py_parse_entry_definition, m)?)?;
    m.add_function(wrap_pyfunction!(py_parse_sopheme_seq, m)?)?;
    m.add_function(wrap_pyfunction!(py_parse_keysymbol_seq, m)?)?;
    m.add_function(wrap_pyfunction!(add_soph_trie_entry, m)?)?;
    m.add_class::<PyChordToSophSearchNode>()?;
    m.add_class::<PyChordToSophSearchResult>()?;
    m.add_class::<PyChordToSophSearchMatch>()?;
    m.add_class::<PySophsToTranslationSearchPath>()?;
    m.add_class::<PyChordToSophSearcher>()?;

    m.add_class::<PyTrie>()?;
    m.add_class::<PyReadonlyTrie>()?;
    m.add_class::<PyNondeterministicTrie>()?;
    m.add_class::<TransitionKey>()?;
    m.add_class::<TransitionCostKey>()?;
    m.add_class::<TransitionCostInfo>()?;
    m.add_class::<TransitionFlag>()?;
    m.add_class::<TransitionFlagManager>()?;
    m.add_class::<TriePath>()?;
    m.add_class::<LookupResult>()?;
    m.add_class::<PyReverseTrieIndex>()?;

    m.add_class::<Soph>()?;
    m.add_class::<TransitionSourceNode>()?;
    m.add_class::<JoinedTriePaths>()?;
    m.add_class::<JoinedTransitionSeq>()?;

    Ok(())
}
