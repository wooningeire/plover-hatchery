pub struct TransitionKey {
    pub src_node_index: usize,
    pub key_id: Option<usize>,
    pub transition_index: usize,
}

pub struct SingleTranslationTransitionKey {
    pub transition_key: TransitionKey,
    pub translation_id: usize,
}