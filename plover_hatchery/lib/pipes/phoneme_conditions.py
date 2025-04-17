from plover_hatchery.lib.sopheme import Sopheme, SophemeSeqPhoneme


def given_sound_has_in_spelling_including_silent(chars: str):
    char_seqs = tuple(chars.split())

    def check(phoneme: SophemeSeqPhoneme):
        start_index_inclusive = phoneme.sopheme_index
        end_index_inclusive = phoneme.sopheme_index

        while start_index_inclusive > 0 and phoneme.seq.sophemes[start_index_inclusive - 1].can_be_silent:
            start_index_inclusive -= 1

        while end_index_inclusive < len(phoneme.seq.sophemes) - 1 and phoneme.seq.sophemes[end_index_inclusive + 1].can_be_silent:
            end_index_inclusive += 1

        spelling_including_silent = Sopheme.get_translation(phoneme.seq.sophemes[start_index_inclusive:end_index_inclusive + 1])
        
        return any(char_seq in spelling_including_silent for char_seq in char_seqs)

    return check


def given_sound_has_stress(threshold: int=1):
    def check(phoneme: SophemeSeqPhoneme):
        return phoneme.keysymbol.stress != 0 and phoneme.keysymbol.stress <= threshold
    
    return check