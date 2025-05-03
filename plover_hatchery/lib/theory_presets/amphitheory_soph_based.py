from plover_hatchery.lib.pipes import *
from plover_hatchery.lib.pipes.types import Soph


def map_phonemes(phoneme: SophemeSeqPhoneme):
    return Soph(phoneme.keysymbol.symbol)

theory = compile_theory(
    soph_trie(map_phonemes, {
        "a": "A",
        "m": "-PL",
        "f": "TP",
        "i": "EU",
        "th": "TH",
        "eir": "E",
        "r": "-R",
    }),
)