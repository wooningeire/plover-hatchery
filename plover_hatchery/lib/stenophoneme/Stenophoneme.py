from enum import Enum, auto

class Sophone(Enum):
    S = auto()
    T = auto()
    K = auto()
    P = auto()
    W = auto()
    H = auto()
    R = auto()

    Z = auto()
    J = auto()
    V = auto()
    D = auto()
    G = auto()
    F = auto()
    N = auto()
    Y = auto()
    B = auto()
    M = auto()
    L = auto()

    CH = auto()
    SH = auto()
    TH = auto()

    NG = auto()

    ANY_VOWEL = auto()

    AA = auto()
    A = auto()
    EE = auto()
    E = auto()
    II = auto()
    I = auto()
    OO = auto()
    O = auto()
    UU = auto()
    U = auto()
    AU = auto()
    OI = auto()
    OU = auto()

    AO = auto()
    AE = auto()

    DUMMY = auto()

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()

vowel_phonemes = {
    Sophone.AA,
    Sophone.A,
    Sophone.EE,
    Sophone.E,
    Sophone.II,
    Sophone.I,
    Sophone.OO,
    Sophone.O,
    Sophone.UU,
    Sophone.U,
    Sophone.AU,
    Sophone.OI,
    Sophone.OU,
    Sophone.AE,
    Sophone.AO,
}