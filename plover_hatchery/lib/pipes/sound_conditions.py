from plover_hatchery.lib.sopheme import Sound


def given_sound_has_in_spelling_including_silent(chars: str):
    char_seqs = tuple(chars.split())

    def check(sound: Sound):
        return any(char_seq in sound.sopheme.chars for char_seq in char_seqs)

    return check


def given_sound_has_stress(threshold: int=1):
    def check(sound: Sound):
        return sound.keysymbol.stress != 0 and sound.keysymbol.stress <= threshold
    
    return check