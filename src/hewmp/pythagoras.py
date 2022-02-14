# coding: utf-8
from enum import Enum
from .monzo import PRIMES
from numpy import zeros


AUGMENTED_INFLECTION = (-11, 7)


class Quality(Enum):
    PERFECT = "P"
    MAJOR = "M"
    MINOR = "m"
    AUGMENTED = "a"
    DIMINISHED = "d"
    NEUTRAL = "N"
    HALF_AUGMENTED = "ha"
    HALF_DIMINISHED = "hd"


class Letter(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    # Extensions
    H = "H"
    # I reserved: One chord in color notation
    J = "J"  # "I" is skipped so that it's not confused with the one (chord) in color notation.
    K = "K"
    # L reserved: Large
    # M reserved: Major
    # N reserved: Neutral
    # O is available
    # P reserved: Perfect
    # Q is available


BASIC_PITCHES = {
    Letter.F: (6, -4),
    Letter.C: (4, -3),
    Letter.G: (3, -2),
    Letter.D: (1, -1),
    Letter.A: (0, 0),
    Letter.E: (-2, 1),
    Letter.B: (-3, 2),
}
REFERENCE_OCTAVE = 4


def read_number(token):
    if token and token[0] in "-+":
        num = token[0]
        token = token[1:]
    else:
        num = ""
    while token and token[0].isdigit():
        num += token[0]
        token = token[1:]
    if num:
        return token, int(num)
    return token, None


class Interval:
    absolute = False
    def __init__(self, quality, interval_class, augmentations=0):
        self.quality = quality
        self.interval_class = interval_class
        self.augmentations = augmentations

    def basic_part(self):
        octaves = (self.interval_class - 1)//7
        basic_class = self.interval_class - octaves*7
        return self.__class__(self.quality, basic_class), octaves

    def monzo(self):
        basic, octaves = self.basic_part()
        twos, threes = BASIC_INTERVALS[basic]
        twos += octaves
        twos += self.augmentations * AUGMENTED_INFLECTION[0]
        threes += self.augmentations * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[0] = twos
        result[1] = threes
        return result

    def __hash__(self):
        return hash((self.quality, self.interval_class, self.augmentations))

    def __eq__(self, other):
        return self.quality == other.quality and self.interval_class == other.interval_class and self.augmentations == other.augmentations

    def __repr__(self):
        return "{}({}, {!r}, {!r})".format(self.__class__.__name__, self.quality, self.interval_class, self.augmentations)

    @classmethod
    def parse(cls, token):
        quality = token[0]
        token = token[1:]
        if quality == "h":
            quality += token[0]
            token = token[1:]
        augmentations = 0
        while token[0] == "a":
            augmentations += 1
            token = token[1:]
        while token[0] == "d":
            augmentations -= 1
            token = token[1:]

        token, interval_class = read_number(token)

        return token, cls(Quality(quality), interval_class, augmentations)


class Pitch:
    absolute = True
    def __init__(self, letter, sharps, octave):
        self.letter = letter
        self.sharps = sharps
        self.octave = octave

    def monzo(self):
        twos, threes = BASIC_PITCHES[self.letter]
        twos += self.octave - REFERENCE_OCTAVE
        twos += self.sharps * AUGMENTED_INFLECTION[0]
        threes += self.sharps * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[0] = twos
        result[1] = threes
        return result

    def __hash__(self):
        return hash((self.letter, self.sharps, self.octave))

    def __eq__(self, other):
        return self.letter == other.letter and self.sharps == other.sharps and self.octave == other.octave

    def __repr__(self):
        "{}({}, {!r}, {!r})".format(self.__class__.__name__, self.sharps, self.octave)


    @classmethod
    def parse(cls, token):
        letter = Letter(token[0])
        token = token[1:]
        token, octave = read_number(token)
        sharps = 0
        while token and token[0] in ACCIDENTALS:
            if token[0] in "#♯":
                sharps += 1
            elif token[0] in "x𝄪":
                sharps += 2
            elif token[0] in "b♭":
                sharps -= 1
            elif token[0] == "𝄫":
                sharps -= 2
            elif token[0] in "t𝄲":
                sharps += 0.5
            elif token[0] in "d𝄳":
                sharps -= 0.5
            token = token[1:]

        if octave is None:
            token, octave = read_number(token)

        return token, cls(letter, sharps, octave)


BASIC_INTERVALS = {
    "d2": (19, -12),
    "d6": (18, -11),
    "d3": (16, -10),
    "d7": (15, -9),
    "d4": (13, -8),
    "d1": (11, -7),
    "d5": (10, -6),
    "m2": (8, -5),
    "m6": (7, -4),
    "m3": (5, -3),
    "m7": (4, -2),
    "P4": (2, -1),
    "P1": (0, 0),
    "P5": (-1, 1),
    "M2": (-3, 2),
    "M6": (-4, 3),
    "M3": (-6, 4),
    "M7": (-7, 5),
    "a4": (-9, 6),
    "a1": (-11, 7),
    "a5": (-12, 8),
    "a2": (-14, 9),
    "a6": (-15, 10),
    "a3": (-17, 11),
    "a7": (-18, 12),

    # Extra half-diminished intervals
    "hd2": (13.5, -8.5),
    "hd6": (12.5, -7.5),
    "hd3": (10.5, -6.5),
    "hd7": (9.5, -5.5),
    "hd4": (7.5, -4.5),
    "hd1": (5.5, -3.5),
    "hd5": (4.5, -2.5),
    # Extra neutral intervals
    "N2": (2.5, -1.5),
    "N6": (1.5, -0.5),
    "N3": (-0.5, 0.5),
    "N7": (-1.5, 1.5),
    # Extra half-augmented intervals
    "ha4": (-3.5, 2.5),
    "ha1": (-5.5, 3.5),
    "ha5": (-6.5, 4.5),
    "ha2": (-8.5, 5.5),
    "ha6": (-9.5, 6.5),
    "ha3": (-11.5, 7.5),
    "ha7": (-12.5, 8.5),
}

items = list(BASIC_INTERVALS.items())
BASIC_INTERVALS = {}
for token, exponents in items:
    _, interval = Interval.parse(token)
    BASIC_INTERVALS[interval] = exponents


INTERVAL_QUALITIES = "dmPNMha"

PITCH_LETTERS = ""

for letter in Letter:
    PITCH_LETTERS += letter.value


ACCIDENTALS = "#xbtd" + "♮♯𝄪♭𝄫𝄲𝄳"
