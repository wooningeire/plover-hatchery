from plover_hatchery.lib.sopheme import SophemeSeqPhoneme


def given_sound_has_in_spelling_including_silent(chars: str):
    char_seqs = tuple(chars.split())

    def check(phoneme: SophemeSeqPhoneme):
        return any(char_seq in phoneme.sopheme.chars for char_seq in char_seqs)

    return check


def given_sound_has_stress(threshold: int=1):
    def check(phoneme: SophemeSeqPhoneme):
        return phoneme.keysymbol.stress != 0 and phoneme.keysymbol.stress <= threshold
    
    return check