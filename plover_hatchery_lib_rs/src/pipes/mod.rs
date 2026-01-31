mod map_def_items;

mod optionalize;
pub use optionalize::optionalize_keysymbols;

mod diphthongs;
pub use diphthongs::add_diphthong_keysymbols;

mod soph_trie;
pub use soph_trie::add_soph_trie_entry;

mod soph;
pub use soph::Soph;