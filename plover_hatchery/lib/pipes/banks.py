from typing import Callable, Generator, TypeVar, Protocol
from dataclasses import dataclass

from plover.steno import Stroke

from ..sopheme import Sound
from ..sophone.Sophone import Sophone
from ..trie import NondeterministicTrie, TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY
from ..theory_defaults.amphitheory import amphitheory
from .state import EntryBuilderState, OutlineSounds, ConsonantVowelGroup
from .join import join, join_on_strokes, tuplify
from .consonants_vowels_enumeration import ConsonantsVowelsEnumerationPlugin


@dataclass
class BanksPlugin:
    class OnComplete(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[str, str], translation: str, new_stroke_node: int, group_index: int, sound_index: int) -> None: ...

    on_vowel_complete: OnComplete


def banks(
    *plugins: BanksPlugin,
    left_chords: Callable[[Sound], Generator[Stroke, None, None]],
    mid_chords: Callable[[Sound], Generator[Stroke, None, None]],
    right_chords: Callable[[Sound], Generator[Stroke, None, None]],
):
    def on_vowel_complete(trie: NondeterministicTrie[str, str], translation: str, new_stroke_node: int, group_index: int, sound_index: int):
        for plugin in plugins:
            plugin.on_vowel_complete(trie=trie, translation=translation, new_stroke_node=new_stroke_node, group_index=group_index, sound_index=sound_index)


    @dataclass
    class State:
        trie: NondeterministicTrie[str, str]
        sounds: OutlineSounds
        translation: str

        left_src_nodes: tuple[int, ...] = ()
        mid_src_nodes: tuple[int, ...] = ()
        right_src_nodes: tuple[int, ...] = ()


    def on_begin(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        left_src_nodes = (trie.ROOT,)

        return State(
            trie,
            sounds,
            translation,

            left_src_nodes=left_src_nodes,
            mid_src_nodes=left_src_nodes,
            right_src_nodes=(),
        )


    def on_consonant(state: State, consonant: Sound, *_, **__):
        left_node = join_on_strokes(state.trie, state.left_src_nodes, left_chords(consonant), state.translation)
        right_node = join_on_strokes(state.trie, state.right_src_nodes, right_chords(consonant), state.translation)

        if left_node is not None and right_node is not None:
            state.trie.link(right_node, left_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))


        state.left_src_nodes = tuplify(left_node)
        state.mid_src_nodes = state.left_src_nodes
        state.right_src_nodes = tuplify(right_node)

    
    def on_vowel(state: State, vowel: Sound, group_index: int, sound_index: int):
        mid_node = join(state.trie, state.mid_src_nodes, (stroke.rtfcre for stroke in mid_chords(vowel)), state.translation)


        if mid_node is not None:
            new_stroke_node = state.trie.get_first_dst_node_else_create(mid_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))
        else:
            new_stroke_node = None


        state.left_src_nodes = tuplify(new_stroke_node)
        state.mid_src_nodes = state.left_src_nodes
        state.right_src_nodes += tuplify(mid_node)

        if new_stroke_node is not None:
            on_vowel_complete(state.trie, state.translation, new_stroke_node, group_index, sound_index)


    def on_complete(state: State):
        for right_src_node in state.right_src_nodes:
            state.trie.set_translation(right_src_node, state.translation)


    return ConsonantsVowelsEnumerationPlugin(
        on_begin=on_begin,
        on_consonant=on_consonant,
        on_vowel=on_vowel,
        on_complete=on_complete,
    )