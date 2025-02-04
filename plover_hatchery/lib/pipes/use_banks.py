from plover.steno import Stroke

from ..sophone.Sophone import Sophone
from ..trie import NondeterministicTrie, TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY
from ..theory_defaults.amphitheory import amphitheory
from .SoundsEnumerator import SoundsEnumerator
from .state import EntryBuilderState, OutlineSounds, ConsonantVowelGroup
from .Hook import Hook

class BanksHooks:
    def __init__(self):
        self.begin: Hook[NondeterministicTrie[str, str]] = Hook()
        self.begin_consonant: Hook[EntryBuilderState] = Hook()
        self.left_node_created: Hook[EntryBuilderState, int, tuple[Stroke, ...], tuple[int, ...]] = Hook()
        self.begin_nonfinal_group: Hook[EntryBuilderState] = Hook()
        self.before_complete_nonfinal_group: Hook[EntryBuilderState] = Hook()
        self.complete_nonfinal_group: "Hook[EntryBuilderState, ConsonantVowelGroup, int | None]" = Hook()
        self.complete_consonant: "Hook[EntryBuilderState, int | None, int | None]" = Hook()
        self.complete_consonant_2: "Hook[EntryBuilderState, int | None, int | None]" = Hook()


def use_banks(enumerator: SoundsEnumerator, chords_raw: dict[str, str]):
    chords = {
        Sophone.__dict__[key]: Stroke.from_steno(steno)
        for key, steno in chords_raw.items()
    }


    hooks = BanksHooks()


    state: EntryBuilderState 

    left_src_nodes: tuple[int, ...] = ()
    mid_src_nodes: tuple[int, ...] = ()
    right_src_nodes: tuple[int, ...] = ()


    @enumerator.begin.listen
    def _(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        nonlocal state
        
        nonlocal left_src_nodes
        nonlocal mid_src_nodes
        nonlocal right_src_nodes

        print(f"entry \"{translation}\"")

        state = EntryBuilderState(trie, sounds, translation)

        left_src_nodes = (trie.ROOT,)
        mid_src_nodes = left_src_nodes
        right_src_nodes = ()

        hooks.begin.emit(trie)


    @enumerator.begin_group.listen
    def _(group_index: int):
        nonlocal mid_src_nodes

        state.group_index = group_index



        # mid_src_nodes = ()
        # if len(group.consonants) == 0 and not state.is_first_consonant_set:
        #     mid_src_nodes = (state.trie.get_first_dst_node_else_create(
        #         left_src_nodes[0],
        #         TRIE_LINKER_KEY,
        #         TransitionCostInfo(0, state.translation)
        #     ),)


    @enumerator.consonant.listen
    def _(consonant_index: int):
        state.phoneme_index = consonant_index

        nonlocal left_src_nodes
        nonlocal mid_src_nodes
        nonlocal right_src_nodes



        hooks.begin_consonant.emit(state)


        left_node = None

        new_left_src_nodes: list[int] = []

        left_strokes = (
            *amphitheory.left_consonant_strokes(state.consonant),
            chords[amphitheory.sound_sophone(state.consonant)],
        )

        for left_src_node in left_src_nodes:
            for stroke in left_strokes:
                if left_node is None:
                    left_node = state.trie.get_first_dst_node_else_create_chain(left_src_node, stroke.keys(), TransitionCostInfo(0, state.translation))
                else:
                    state.trie.link_chain(left_src_node, left_node, stroke.keys(), TransitionCostInfo(0, state.translation))



        if left_node is not None:
            hooks.left_node_created.emit(state, left_node, left_strokes, left_src_nodes)
                

            new_left_src_nodes.append(left_node)


        right_node = None

        new_right_src_nodes: list[int] = []

        right_strokes = (
            # *amphitheory.left_consonant_strokes(state.consonant),
            amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT[amphitheory.sound_sophone(state.consonant)],
        ) if amphitheory.sound_sophone(state.consonant) in amphitheory.spec.PHONEMES_TO_CHORDS_RIGHT else ()

        for right_src_node in right_src_nodes:
            for stroke in right_strokes:
                if right_node is None:
                    right_node = state.trie.get_first_dst_node_else_create_chain(right_src_node, stroke.keys(), TransitionCostInfo(0, state.translation))
                else:
                    state.trie.link_chain(right_src_node, right_node, stroke.keys(), TransitionCostInfo(0, state.translation))

        if right_node is not None:
            # hooks.right_node_created.emit(state, right_node, strokes, right_src_nodes)
                

            new_right_src_nodes.append(right_node)

        if left_node is not None and right_node is not None:
            state.trie.link(right_node, left_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))


        hooks.complete_consonant.emit(state, left_node, right_node)
        hooks.complete_consonant_2.emit(state, left_node, right_node)


        left_src_nodes = tuple(new_left_src_nodes)
        mid_src_nodes = left_src_nodes
        right_src_nodes = tuple(new_right_src_nodes)

    
    @enumerator.vowel.listen
    def _(group: ConsonantVowelGroup):
        nonlocal left_src_nodes
        nonlocal mid_src_nodes
        nonlocal right_src_nodes

        state.phoneme_index = len(group.consonants)


        mid_node = None

        for mid_src_node in mid_src_nodes:
            if mid_node is None:
                mid_node = state.trie.get_first_dst_node_else_create(mid_src_node, amphitheory.spec.vowel_to_steno(group.vowel), TransitionCostInfo(0, state.translation))
            else:
                state.trie.link(mid_src_node, mid_node, amphitheory.spec.vowel_to_steno(group.vowel), TransitionCostInfo(0, state.translation))


        if mid_node is not None:
            new_stroke_node = state.trie.get_first_dst_node_else_create(mid_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))
        else:
            new_stroke_node = None

        hooks.before_complete_nonfinal_group.emit(state)

        hooks.complete_nonfinal_group.emit(state, group, new_stroke_node)




        left_src_nodes = (new_stroke_node,) if new_stroke_node is not None else ()
        mid_src_nodes = left_src_nodes
        right_src_nodes += (mid_node,) if mid_node is not None else ()



    @enumerator.complete.listen
    def _():
        for right_src_node in right_src_nodes:
            state.trie.set_translation(right_src_node, state.translation)


    return hooks