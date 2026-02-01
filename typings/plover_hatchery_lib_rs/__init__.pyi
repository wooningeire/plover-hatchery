from collections.abc import Callable, Sequence
from typing import Any, Literal, final


class Keysymbol:
    @property
    def symbol(self) -> str: ...
    @property
    def base_symbol(self) -> str: ...
    @property
    def stress(self) -> int: ...
    @property
    def optional(self) -> bool: ...

    def __init__(self, symbol: str, stress: int, optional: bool, /) -> None: ...

    @staticmethod
    def new_with_known_base_symbol(symbol: str, base_symbol: str, stress: int, optional: bool, /) -> Keysymbol: ...

    @property
    def is_vowel(self) -> bool: ...

    @property
    def is_consonant(self) -> bool: ...


class Sopheme:
    @property
    def chars(self) -> str: ...
    @property
    def keysymbols(self) -> list[Keysymbol]: ...

    def __init__(self, chars: str, keysymbols: list[Keysymbol], /) -> None: ...

    @property
    def can_be_silent(self) -> bool: ...


class Transclusion:
    @property
    def target_varname(self) -> str: ...
    @property
    def stress(self) -> int: ...

    def __init__(self, target_varname: str, stress: int, /) -> None: ...

class Entity:
    class Sopheme(Entity):
        def __init__(self, sopheme: Sopheme, /) -> None: ...

    class Transclusion(Entity):
        def __init__(self, transclusion: Transclusion, /) -> None: ...

    class RawDef(Entity):
        def __init__(self, definition: Def, /) -> None: ...

class Def:
    @property
    def entities(self) -> list[Entity]: ...
    @property
    def varname(self) -> str: ...

    def __init__(self, entities: Sequence[Entity], varname: str, /) -> None: ...

class DefDict:
    def add(self, varname: str, definition: Sequence[Entity], /) -> None: ...
    def get_def(self, varname: str, /) -> Def: ...
    def foreach_key(self, callable: Callable[[str], None], /) -> None: ...


class SophemeSeq:
    @property
    def sophemes(self) -> list[Sopheme]: ...

    def __init__(self, sophemes: Sequence[Sopheme], /) -> None: ...

class DefView:
    @property
    def defs(self) -> DefDict: ...
    @property
    def root_def(self) -> Def: ...

    def __init__(self, defs: DefDict, base_def: Def, /) -> None: ...
    def collect_sophemes(self) -> SophemeSeq: ...
    def translation(self) -> str: ...

    def foreach(self, callable: Callable[[DefViewCursor], None], /) -> None: ...
    def foreach_keysymbol(self, callable: Callable[[DefViewCursor, Keysymbol], None], /) -> None: ...

    @property
    def first_consonant_cur(self) -> tuple[int, ...] | None: ...
    @property
    def last_consonant_cur(self) -> tuple[int, ...] | None: ...
    @property
    def first_vowel_cur(self) -> tuple[int, ...] | None: ...
    @property
    def last_vowel_cur(self) -> tuple[int, ...] | None: ...


class DefViewItem:
    @property
    def n_children(self) -> int: ...

    def keysymbol(self) -> Keysymbol: ...
    def sopheme(self) -> Sopheme: ...

    @final
    class Keysymbol(DefViewItem):
        __match_args__ = ("__keysymbol",)

        __keysymbol: Keysymbol
        def __init__(self, keysymbol: Keysymbol, /) -> None: ...

    @final
    class Sopheme(DefViewItem):
        __match_args__ = ("__sopheme",)

        __sopheme: Sopheme
        def __init__(self, sopheme: Sopheme, /) -> None: ...

class DefViewCursor:
    def __init__(self, view: DefView, index_stack: Sequence[int], /) -> None: ...

    @property
    def view(self) -> DefView: ...
    @property
    def index_stack(self) -> tuple[int, ...]: ...

    def tip(self) -> DefViewItem: ...
    def maybe_tip(self) -> DefViewItem | None: ...
    
    def nth(self, level: int, /) -> DefViewItem: ...
    def maybe_nth(self, level: int, /) -> DefViewItem | None: ...

    def next_keysymbol_cur(self) -> DefViewCursor | None: ...
    def prev_keysymbol_cur(self) -> DefViewCursor | None: ...

    def occurs_before_first_consonant(self) -> bool: ...
    def occurs_after_last_consonant(self) -> bool: ...
    def occurs_before_first_vowel(self) -> bool: ...
    def occurs_after_last_vowel(self) -> bool: ...

    @property
    def stack_len(self) -> int: ...

    def spelling_including_silent(self) -> str: ...

def optionalize_keysymbols(view: DefView, condition: Callable[[DefViewCursor], bool], /) -> Def: ...
def add_diphthong_keysymbols(view: DefView, map_keysymbols: Callable[[DefViewCursor], Sequence[Keysymbol]], /) -> Def: ...

class AffixKey:
    def __init__(self, is_suffix: bool, name: str, phono: str, ortho: str) -> None: ...

    @property
    def is_suffix(self) -> bool: ...
    @property
    def name(self) -> str: ...
    @property
    def phono(self) -> str: ...
    @property
    def ortho(self) -> str: ...

    

def parse_entry_definition(seq: str, /) -> list[Entity]:
    """Parse a string into a list of Entity objects (Sophemes and Transclusions)."""
    ...

def parse_sopheme_seq(seq: str, /) -> list[Sopheme]:
    """Parse a string into a list of Sopheme objects."""
    ...

def parse_keysymbol_seq(seq: str, /) -> list[Keysymbol]:
    """Parse a string into a list of Keysymbol objects."""
    ...


def add_soph_trie_entry(
    trie: NondeterministicTrie,
    entry_id: int,
    view: DefView,
    map_to_sophs: Callable[[DefViewCursor], set[Soph]],
    get_key_ids_else_create: Callable[[DefViewCursor], Sequence[int]],
    register_transition: Callable[[TransitionKey, int, DefViewCursor], None],
    transition_flags: TransitionFlagManager,
    skip_transition_flag_id: int,
    emit_begin_add_entry: Callable[[int], None],
    emit_add_soph_transition: Callable[[int, int, int], None],
) -> None: ...


class NondeterministicTrie:
    ROOT: int

    def __init__(self, /) -> None: ...

    def follow(
        self,
        src_node_id: int,
        key_id: int | None,
        cost: float,
        translation_id: int,
        /,
    ) -> TriePath: ...

    def follow_chain(
        self,
        src_node_id: int,
        key_ids: Sequence[int | None],
        cost: float,
        translation_id: int,
        /,
    ) -> TriePath: ...

    def link(
        self,
        src_node_id: int,
        dst_node_id: int,
        key_id: int | None,
        cost: float,
        translation_id: int,
        /,
    ) -> TransitionKey: ...

    def link_chain(
        self,
        src_node_id: int,
        dst_node_id: int,
        key_ids: Sequence[int | None],
        cost: float,
        translation_id: int,
        /,
    ) -> list[TransitionKey]: ...

    def link_join(
        self,
        src_nodes: Sequence[TransitionSourceNode],
        dst_node_id: int | None,
        key_ids: Sequence[int | None],
        translation_id: int,
        /,
    ) -> JoinedTriePaths: ...

    def link_join_chain(
        self,
        src_nodes: Sequence[TransitionSourceNode],
        dst_node_id: int | None,
        key_id_chains: Sequence[Sequence[int | None]],
        translation_id: int,
        /,
    ) -> JoinedTriePaths: ...

    def set_translation(self, node_id: int, translation_id: int, /) -> None: ...

    def traverse(
        self,
        src_node_paths: Sequence[TriePath],
        key_id: int | None,
        /,
    ) -> list[TriePath]: ...

    def traverse_chain(
        self,
        src_node_paths: Sequence[TriePath],
        key_ids: Sequence[int | None],
        /,
    ) -> list[TriePath]: ...

    def get_translations_and_costs_single(
        self,
        node_id: int,
        transitions: Sequence[TransitionKey],
        /,
    ) -> list[tuple[int, float]]: ...

    def get_translations_and_costs(
        self,
        node_paths: Sequence[TriePath],
        /,
    ) -> list[LookupResult]: ...

    def get_transition_cost(
        self,
        transition: TransitionKey,
        translation_id: int,
        /,
    ) -> float | None: ...

    def transition_has_key(
        self,
        transition: TransitionKey,
        key_id: int | None,
        /,
    ) -> bool: ...

    def get_translations_and_min_costs(
        self,
        node_paths: Sequence[TriePath],
        /,
    ) -> list[LookupResult]: ...

    def get_all_translation_ids(self, /) -> list[int]: ...

    def n_nodes(self, /) -> int: ...

    def transition_has_cost_for_translation(
        self,
        src_node_id: int,
        key_id: int | None,
        transition_index: int,
        translation_id: int,
        /,
    ) -> bool: ...

    def create_reverse_index(self, /) -> ReverseTrieIndex: ...


class TransitionKey:
    @property
    def src_node_index(self) -> int: ...
    @property
    def key_id(self) -> int | None: ...
    @property
    def transition_index(self) -> int: ...

    def __init__(
        self,
        src_node_index: int,
        key_id: int | None,
        transition_index: int,
        /,
    ) -> None: ...

class TransitionCostKey:
    @property
    def transition_key(self) -> TransitionKey: ...
    @property
    def translation_id(self) -> int: ...

    def __init__(
        self,
        transition_key: TransitionKey,
        translation_id: int,
        /,
    ) -> None: ...

class TransitionCostInfo:
    @property
    def cost(self) -> float: ...
    @property
    def translation_id(self) -> int: ...

    def __init__(
        self,
        cost: float,
        translation_id: int,
        /,
    ) -> None: ...

class TriePath:
    @property
    def dst_node_id(self) -> int: ...
    @property
    def transitions(self) -> list[TransitionKey]: ...

    def __init__(
        self,
        dst_node_id: int = 0,
        transitions: Sequence[TransitionKey] = ...,
        /,
    ) -> None: ...

    @staticmethod
    def root() -> "TriePath": ...


class LookupResult:
    @property
    def translation_id(self) -> int: ...
    @property
    def cost(self) -> float: ...
    @property
    def transitions(self) -> list[TransitionKey]: ...

    def __init__(
        self,
        translation_id: int,
        cost: float,
        transitions: Sequence[TransitionKey],
        /,
    ) -> None: ...

class ReverseTrieIndex:
    def get_sequences(self, trie: NondeterministicTrie, translation_id: int, /) -> list[LookupResult]: ...
    def get_subtrie_data(self, trie: NondeterministicTrie, translation_id: int, /) -> dict[str, Any] | None: ...


class Soph:
    @property
    def value(self) -> str: ...
    
    def __init__(self, value: str, /) -> None: ...
    
    @staticmethod
    def parse_seq(seq: str, /) -> tuple[Soph, ...]: ...


class TransitionSourceNode:
    @property
    def src_node_index(self) -> int: ...
    @property
    def outgoing_cost(self) -> float: ...
    @property
    def outgoing_transition_flags(self) -> list[int]: ...
    
    def __init__(self, src_node_index: int, outgoing_cost: float = 0.0, outgoing_transition_flags: Sequence[int] = ..., /) -> None: ...
    
    @staticmethod
    def root() -> TransitionSourceNode: ...
    
    @staticmethod
    def increment_costs(srcs: Sequence[TransitionSourceNode], cost_change: float, /) -> list[TransitionSourceNode]: ...
    
    @staticmethod
    def add_flags(srcs: Sequence[TransitionSourceNode], flags: Sequence[int], /) -> list[TransitionSourceNode]: ...


class JoinedTransitionSeq:
    @property
    def transitions(self) -> list[TransitionKey]: ...
    
    def __init__(self, transitions: Sequence[TransitionKey], /) -> None: ...


class JoinedTriePaths:
    @property
    def dst_node_id(self) -> int | None: ...
    @property
    def transition_seqs(self) -> list[JoinedTransitionSeq]: ...
    
    def __init__(self, dst_node_id: int | None, transition_seqs: Sequence[JoinedTransitionSeq], /) -> None: ...


class TransitionFlag:
    def __init__(self, /) -> None: ...

class TransitionFlagManager:
    def __init__(self, /) -> None: ...
    def new_flag(self, label: str, /) -> int: ...
    def get_label(self, flag: int, /) -> str: ...
    def get_flags(self, cost_key: TransitionCostKey, /) -> list[int]: ...
