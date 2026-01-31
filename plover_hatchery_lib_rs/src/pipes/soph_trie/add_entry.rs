use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};

use crate::trie::{
    TransitionSourceNode,
    JoinedTriePaths,
    TransitionCostKey,
    TransitionFlagManager,
    py::PyNondeterministicTrie,
};
use crate::defs::py::{PyDefView, PyDefViewCursor, PyDefViewItem};


/// Stack item for tracking cursor position and source nodes during entry building.
struct SourceNodePositionStackItem {
    cursor: PyDefViewCursor,
    source_nodes: Vec<TransitionSourceNode>,
}

/// Add an entry to the soph trie.
///
/// This is a structural port of the Python `add_entry` logic from `soph_trie.py`.
/// It iterates over a DefView, building trie transitions for each keysymbol.
///
/// # Arguments
/// * `trie` - The nondeterministic trie to add entries to
/// * `entry_id` - The unique ID for this entry (translation_id)
/// * `view` - The DefView containing the sophemes and keysymbols
/// * `map_to_sophs` - Callback to get sophs from a cursor position
/// * `get_key_ids_else_create` - Callback to get or create key IDs for a set of sophs
/// * `register_transition` - Callback to register a transition with phoneme data
/// * `transition_flags` - The transition flag manager
/// * `skip_transition_flag_id` - The flag ID for skip transitions
/// * `emit_begin_add_entry` - Hook callback for begin_add_entry event
/// * `emit_add_soph_transition` - Hook callback for add_soph_transition event
#[pyfunction]
pub fn add_soph_trie_entry(
    trie: Py<PyNondeterministicTrie>,
    entry_id: usize,
    view: Py<PyDefView>,
    map_to_sophs: Py<PyAny>,
    get_key_ids_else_create: Py<PyAny>,
    register_transition: Py<PyAny>,
    transition_flags: Py<TransitionFlagManager>,
    skip_transition_flag_id: usize,
    emit_begin_add_entry: Py<PyAny>,
    emit_add_soph_transition: Py<PyAny>,
    py: Python,
) -> PyResult<()> {
    let kwargs = PyDict::new(py);
    kwargs.set_item("trie", trie.clone_ref(py))?;
    kwargs.set_item("entry_id", entry_id)?;
    let states = emit_begin_add_entry.call(py, (), Some(&kwargs))?;


    // The nodes from which the next transition will depart
    let mut source_nodes: Vec<TransitionSourceNode> = vec![TransitionSourceNode::root()];
    // The stack of source nodes and cursor positions for tracking nested structures in a Def
    let mut source_node_position_stack: Vec<SourceNodePositionStackItem> = vec![];
    // The latest destination node ID for joined paths
    let mut last_dst_node_id: Option<usize> = None;


    let step_in = |
        cursor: &PyDefViewCursor,
        source_nodes: &Vec<TransitionSourceNode>,
        source_node_position_stack: &mut Vec<SourceNodePositionStackItem>,
    | -> PyResult<()> {
        while cursor.stack_len() > source_node_position_stack.len() {
            source_node_position_stack.push(SourceNodePositionStackItem {
                cursor: PyDefViewCursor::new(
                    cursor.view.clone_ref(py),
                    cursor.index_stack(py)?.extract::<Vec<usize>>()?,
                ),
                source_nodes: source_nodes.clone(),
            });
        }

        Ok(())
    };


    let step_out = |
        py: Python,
        n_steps: usize,
        source_nodes: &mut Vec<TransitionSourceNode>,
        source_node_position_stack: &mut Vec<SourceNodePositionStackItem>,
        last_dst_node_id: &mut Option<usize>,
        trie: &Py<PyNondeterministicTrie>,
        entry_id: usize,
        map_to_sophs: &Py<PyAny>,
        get_key_ids_else_create: &Py<PyAny>,
        register_transition: &Py<PyAny>,
        transition_flags: &Py<TransitionFlagManager>,
        skip_transition_flag_id: usize,
        emit_add_soph_transition: &Py<PyAny>,
        states: &Py<PyAny>,
    | -> PyResult<()> {
        let mut has_keysymbols = false;
        let mut new_source_nodes: Vec<TransitionSourceNode> = vec![];

        let mut join_dst_node_id: Option<usize> = None;

        for _ in 0..n_steps {
            let SourceNodePositionStackItem {
                cursor: old_cursor,
                source_nodes: old_source_nodes,
            } = source_node_position_stack.pop().ok_or_else(|| {
                pyo3::exceptions::PyRuntimeError::new_err("Stack underflow in step_out")
            })?;

            let maybe_tip = old_cursor.maybe_tip(py)?;

            match maybe_tip {
                Some(PyDefViewItem::Keysymbol(keysymbol)) => {
                    has_keysymbols = true;

                    if keysymbol.optional() {
                        let incremented = TransitionSourceNode::increment_costs(old_source_nodes.clone(), 5.0);
                        let with_flags = TransitionSourceNode::add_flags(incremented, vec![skip_transition_flag_id]);
                        new_source_nodes.extend(with_flags);
                    }
                }

                _ => {
                    if !has_keysymbols {
                        new_source_nodes.extend(old_source_nodes.clone());
                    }
                }
            }


            let py_cursor = old_cursor.clone();
            let py_sophs = map_to_sophs.call1(py, (py_cursor,))?;

            let key_ids_result = get_key_ids_else_create.call1(py, (&py_sophs,))?;
            let key_ids: Vec<Option<usize>> = key_ids_result.extract(py)?;

            let paths: JoinedTriePaths = {
                let mut trie_mut = trie.borrow_mut(py);
                trie_mut.trie.link_join(
                    &old_source_nodes,
                    join_dst_node_id,
                    &key_ids,
                    entry_id,
                )
            };

            // If we already have a previous join destination node, then we can reuse that node
            // as the destination for the next join
            if join_dst_node_id.is_none() && paths.dst_node_id.is_some() {
                join_dst_node_id = paths.dst_node_id;
            }

            for seq in &paths.transition_seqs {
                if !seq.transitions.is_empty() {
                    let first_transition = seq.transitions[0];
                    register_transition.call1(py, (first_transition, entry_id, old_cursor.clone()))?;
                }

                for transition in &seq.transitions {
                    // # TODO could optimize this linear search
                    let should_add_flag = old_source_nodes.iter().any(|old_src_node| {
                        old_src_node.src_node_index == transition.src_node_index
                            && old_src_node.outgoing_transition_flags.contains(&skip_transition_flag_id)
                    });

                    if should_add_flag {
                        let cost_key = TransitionCostKey::new(*transition, entry_id);
                        transition_flags.borrow_mut(py).flag_transition(cost_key, skip_transition_flag_id);
                    }
                }
            }

            let kwargs = PyDict::new(py);
            kwargs.set_item("cursor", old_cursor.clone())?;
            kwargs.set_item("sophs", &py_sophs)?;
            kwargs.set_item("paths", paths.clone())?;
            kwargs.set_item("node_srcs", PyTuple::new(py, old_source_nodes.clone())?)?;
            kwargs.set_item("new_node_srcs", source_nodes.clone())?;
            kwargs.set_item("trie", trie.clone_ref(py))?;
            kwargs.set_item("entry_id", entry_id)?;

            emit_add_soph_transition.call(py, (states.clone_ref(py),), Some(&kwargs))?;
        }

        if let Some(dst) = join_dst_node_id {
            new_source_nodes.push(TransitionSourceNode::new(dst, 0.0, vec![]));
            *last_dst_node_id = Some(dst);
        }

        *source_nodes = new_source_nodes;

        Ok(())
    };

    

    let mut foreach_result = Ok(());

    view.borrow(py).with_rs_result(py, |view_rs| {
        view_rs.foreach(|_, cur| {
            let cursor = PyDefViewCursor::of(view.clone_ref(py), &cur);
            let cursor_stack_len = cursor.stack_len();

            if cursor_stack_len <= source_node_position_stack.len() {
                let n_steps = source_node_position_stack.len() - cursor_stack_len + 1;

                if let Err(err) = step_out(
                    py,
                    n_steps,
                    &mut source_nodes,
                    &mut source_node_position_stack,
                    &mut last_dst_node_id,
                    &trie,
                    entry_id,
                    &map_to_sophs,
                    &get_key_ids_else_create,
                    &register_transition,
                    &transition_flags,
                    skip_transition_flag_id,
                    &emit_add_soph_transition,
                    &states,
                ) {
                    foreach_result = Err(err);
                    return;
                }
            }

            if let Err(err) = step_in(&cursor, &source_nodes, &mut source_node_position_stack) {
                foreach_result = Err(err);
            }
        })
    })?;

    foreach_result?;


    let remaining_steps = source_node_position_stack.len();
    if remaining_steps > 0 {
        step_out(
            py,
            remaining_steps,
            &mut source_nodes,
            &mut source_node_position_stack,
            &mut last_dst_node_id,
            &trie,
            entry_id,
            &map_to_sophs,
            &get_key_ids_else_create,
            &register_transition,
            &transition_flags,
            skip_transition_flag_id,
            &emit_add_soph_transition,
            &states,
        )?;
    }

    if let Some(dst_node_id) = last_dst_node_id {
        trie.borrow_mut(py).trie.set_translation(dst_node_id, entry_id);
    }

    Ok(())
}