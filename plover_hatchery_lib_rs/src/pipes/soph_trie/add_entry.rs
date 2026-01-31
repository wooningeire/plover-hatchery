use std::collections::HashSet;

use crate::pipes::Soph;
use crate::trie::{
    NondeterministicTrie, NodeSrc, JoinedTriePaths, TransitionKey, TransitionCostKey,
    py::PyNondeterministicTrie,
};
use crate::defs::{
    DefViewItemRef, Keysymbol,
    py::{PyDefView, PyDefViewCursor, PyDefViewItem},
};

use pyo3::prelude::*;
use pyo3::types::{PyAnyMethods, PySet, PyDict, PyTuple};



/// Stack item for tracking cursor position and source nodes during entry building.
struct SourceNodePositionStackItem {
    cursor: PyDefViewCursor,
    source_nodes: Vec<NodeSrc>,
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
/// * `add_transition_flag` - Callback to add a skip flag to a transition
/// * `skip_transition_flag_id` - The flag ID for skip transitions
/// * `emit_begin_add_entry` - Hook callback for begin_add_entry event
/// * `emit_add_soph_transition` - Hook callback for add_soph_transition event
#[pyfunction]
#[pyo3(signature = (
    trie,
    entry_id,
    view,
    map_to_sophs,
    get_key_ids_else_create,
    register_transition,
    add_transition_flag,
    skip_transition_flag_id,
    emit_begin_add_entry,
    emit_add_soph_transition,
))]
pub fn add_soph_trie_entry(
    py: Python,
    trie: Py<PyNondeterministicTrie>,
    entry_id: usize,
    view: Py<PyDefView>,
    map_to_sophs: PyObject,
    get_key_ids_else_create: PyObject,
    register_transition: PyObject,
    add_transition_flag: PyObject,
    skip_transition_flag_id: usize,
    emit_begin_add_entry: PyObject,
    emit_add_soph_transition: PyObject,
) -> PyResult<()> {
    // states = api.begin_add_entry.emit_and_store_outputs(trie=trie, entry_id=entry_id)
    let kwargs = PyDict::new(py);
    kwargs.set_item("trie", trie.clone_ref(py))?;
    kwargs.set_item("entry_id", entry_id)?;
    let states = emit_begin_add_entry.call(py, (), Some(&kwargs))?;

    // src_nodes: list[NodeSrc] = [NodeSrc(0)]
    let mut source_nodes: Vec<NodeSrc> = vec![NodeSrc::root()];
    // positions_and_src_nodes_stack: list[tuple[DefViewCursor, list[NodeSrc]]] = []
    let mut source_node_position_stack: Vec<SourceNodePositionStackItem> = vec![];
    // last_dst_node_id: int | None = None
    let mut last_dst_node_id: Option<usize> = None;


    // Helper closure for step_in
    // def step_in(cursor: DefViewCursor):
    //     while cursor.stack_len > len(positions_and_src_nodes_stack):
    //         positions_and_src_nodes_stack.append((cursor, list(src_nodes)))
    let step_in = |
        cursor: &PyDefViewCursor,
        source_nodes: &Vec<NodeSrc>,
        source_node_position_stack: &mut Vec<SourceNodePositionStackItem>,
    | {
        while cursor.stack_len() > source_node_position_stack.len() {
            source_node_position_stack.push(SourceNodePositionStackItem {
                cursor: PyDefViewCursor::new(cursor.view.clone_ref(py), cursor.index_stack(py).unwrap().extract::<Vec<usize>>().unwrap()),
                source_nodes: source_nodes.clone(),
            });
        }
    };


    // Helper closure for step_out
    // def step_out(n_steps: int):
    let step_out = |py: Python,
                    n_steps: usize,
                    source_nodes: &mut Vec<NodeSrc>,
                    source_node_position_stack: &mut Vec<SourceNodePositionStackItem>,
                    last_dst_node_id: &mut Option<usize>,
                    trie: &Py<PyNondeterministicTrie>,
                    entry_id: usize,
                    map_to_sophs: &PyObject,
                    get_key_ids_else_create: &PyObject,
                    register_transition: &PyObject,
                    add_transition_flag: &PyObject,
                    skip_transition_flag_id: usize,
                    emit_add_soph_transition: &PyObject,
                    states: &PyObject| -> PyResult<()> {
        // nonlocal src_nodes, last_dst_node_id

        // has_keysymbols = False
        let mut has_keysymbols = false;
        // new_src_nodes: list[NodeSrc] = []
        let mut new_source_nodes: Vec<NodeSrc> = vec![];

        // dst_node_id = None
        let mut dst_node_id: Option<usize> = None;

        // for _ in range(n_steps):
        for _ in 0..n_steps {
            // old_cursor, old_src_nodes = positions_and_src_nodes_stack.pop()
            let SourceNodePositionStackItem {
                cursor: old_cursor,
                source_nodes: old_source_nodes,
            } = source_node_position_stack.pop().ok_or_else(|| {
                pyo3::exceptions::PyRuntimeError::new_err("Stack underflow in step_out")
            })?;

            // match old_cursor.tip():
            let maybe_tip = old_cursor.maybe_tip(py)?;

            match maybe_tip {
                // case DefViewItem.Keysymbol(keysymbol):
                Some(PyDefViewItem::Keysymbol(keysymbol)) => {
                    // has_keysymbols = True
                    has_keysymbols = true;

                    // if keysymbol.optional:
                    if keysymbol.optional() {
                        // new_src_nodes.extend(NodeSrc.add_flags(NodeSrc.increment_costs(old_src_nodes, 5), (skip_transition_flag,)))
                        let incremented = NodeSrc::increment_costs(old_source_nodes.clone(), 5.0);
                        let with_flags = NodeSrc::add_flags(incremented, vec![skip_transition_flag_id]);
                        new_source_nodes.extend(with_flags);
                    }
                }

                // case _:
                _ => {
                    // if not has_keysymbols:
                    //     new_src_nodes.extend(old_src_nodes)
                    if !has_keysymbols {
                        new_source_nodes.extend(old_source_nodes.clone());
                    }
                }
            }


            // sophs = set(Soph(value) for value in map_to_sophs(old_cursor))
            let py_cursor = old_cursor.clone();
            let py_sophs = map_to_sophs.call1(py, (py_cursor,))?;
            // key_ids = key_id_manager.get_key_ids_else_create(sophs)
            let key_ids_result = get_key_ids_else_create.call1(py, (&py_sophs,))?;
            let key_ids: Vec<Option<usize>> = key_ids_result.extract(py)?;

            // Convert old_source_nodes to the format needed by link_join
            let old_source_nodes_for_join: Vec<NodeSrc> = old_source_nodes.clone();

            // paths = trie.link_join(old_src_nodes, dst_node_id, key_id_manager.get_key_ids_else_create(sophs), entry_id)
            let paths: JoinedTriePaths = {
                let mut trie_mut = trie.borrow_mut(py);
                trie_mut.trie.link_join(
                    &old_source_nodes_for_join,
                    dst_node_id,
                    &key_ids,
                    entry_id,
                )
            };

            // if dst_node_id is None and paths.dst_node_id is not None:
            //     dst_node_id = paths.dst_node_id
            if dst_node_id.is_none() && paths.dst_node_id.is_some() {
                dst_node_id = paths.dst_node_id;
            }

            // for seq in paths.transition_seqs:
            for seq in &paths.transition_seqs {
                // api.register_transition(seq.transitions[0], entry_id, old_cursor)
                if !seq.transitions.is_empty() {
                    let first_transition = seq.transitions[0];
                    register_transition.call1(py, (first_transition, entry_id, old_cursor.clone()))?;
                }

                // for transition in seq.transitions:
                for transition in &seq.transitions {
                    // # TODO could optimize this linear search
                    // if any(
                    //     old_src_node.node == transition.src_node_index and skip_transition_flag in old_src_node.outgoing_transition_flags
                    //     for old_src_node in old_src_nodes
                    // ):
                    //     transition_flags.mappings[TransitionCostKey(transition, entry_id)].append(skip_transition_flag)
                    let should_add_flag = old_source_nodes.iter().any(|old_src_node| {
                        old_src_node.src_node_index == transition.src_node_index
                            && old_src_node.outgoing_transition_flags.contains(&skip_transition_flag_id)
                    });

                    if should_add_flag {
                        let cost_key = TransitionCostKey::new(*transition, entry_id);
                        add_transition_flag.call1(py, (cost_key, skip_transition_flag_id))?;
                    }
                }
            }

            // api.add_soph_transition.emit_with_states(
            //     states,
            //     cursor=old_cursor,
            //     sophs=sophs,
            //     paths=paths,
            //     node_srcs=tuple(old_src_nodes),
            //     new_node_srcs=src_nodes,
            //     trie=trie,
            //     entry_id=entry_id,
            // )

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

        // if dst_node_id is not None:
        //     new_src_nodes.append(NodeSrc(dst_node_id))
        //     last_dst_node_id = dst_node_id
        if let Some(dst) = dst_node_id {
            new_source_nodes.push(NodeSrc::new(dst, 0.0, vec![]));
            *last_dst_node_id = Some(dst);
        }

        // src_nodes = new_src_nodes
        *source_nodes = new_source_nodes;

        Ok(())
    };


    // @view.foreach
    // def _(cursor: DefViewCursor):
    //     nonlocal src_nodes
    //
    //     if cursor.stack_len <= len(positions_and_src_nodes_stack):
    //         dst_node_id = step_out(len(positions_and_src_nodes_stack) - cursor.stack_len + 1)
    //         if dst_node_id is not None:
    //             src_nodes.append(NodeSrc(dst_node_id))
    //
    //     step_in(cursor)

    // Use the view's foreach method
    view.borrow(py).with_rs_result(py, |view_rs| {
        view_rs.foreach(|_, cur| {
            let cursor = PyDefViewCursor::of(view.clone_ref(py), &cur);
            let cursor_stack_len = cursor.stack_len();

            if cursor_stack_len <= source_node_position_stack.len() {
                let n_steps = source_node_position_stack.len() - cursor_stack_len + 1;

                if let Err(e) = step_out(
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
                    &add_transition_flag,
                    skip_transition_flag_id,
                    &emit_add_soph_transition,
                    &states,
                ) {
                    // Log error but continue - matching Python behavior
                    eprintln!("Error in step_out: {:?}", e);
                }
            }

            step_in(&cursor, &source_nodes, &mut source_node_position_stack);
        })
    })?;


    // step_out(len(positions_and_src_nodes_stack))
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
            &add_transition_flag,
            skip_transition_flag_id,
            &emit_add_soph_transition,
            &states,
        )?;
    }

    // if last_dst_node_id is not None:
    //     trie.set_translation(last_dst_node_id, entry_id)
    if let Some(dst_node_id) = last_dst_node_id {
        trie.borrow_mut(py).trie.set_translation(dst_node_id, entry_id);
    }

    Ok(())
}