from numpy import array, zeros
from .arrow import SignedArrow as SA
from .monzo import PRIMES
from .pythagoras import Quality, Letter
from . import pythagoras


AUGMENTED_INFLECTION = (-12, 3.5)


INFLECTIONS = {
    SA("+-"): [-4, 0, 1, 0, 0.5],
    SA("><"): [8, 0, 0, -1, -1.5],
    SA("^v"): [-5, 1, 0, 0, 1],
    SA("i!"): [2, 0, 0, 0, 0.5, -1],
    SA("*%"): [-11, 0, 0, 0, 2, 0, 1],
    SA("AV"): [6, 0, 0, 0, -0.5, 0, 0, -1],
    SA("un"): [8, 0, 0, 0, -1, 0, 0, 0, -1],
    SA("UD"): [-10, 0, 0, 0, 1.5, 0, 0, 0, 0, 1],
    SA("MW"): [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1],
}

for key, value in list(INFLECTIONS.items()):
    INFLECTIONS[key] = array(value + [0] * (len(PRIMES) - len(value)))


BASIC_INTERVALS = {
    "d4": (21, -6),
    "d2": (19, -5.5),
    "d7": (18, -5),
    "d5": (16, -4.5),
    "d3": (14, -4),
    "d1": (12, -3.5),
    "d6": (11, -3),
    "m4": (9, -2.5),
    "m2": (7, -2),
    "m7": (6, -1.5),
    "m5": (4, -1),
    "P3": (2, -0.5),
    "P1": (0, 0),
    "P6": (-1, 0.5),
    "M4": (-3, 1),
    "M2": (-5, 1.5),
    "M7": (-6, 2),
    "M5": (-8, 2.5),
    "a3": (-10, 3),
    "a1": (-12, 3.5),
    "a6": (-13, 4),
    "a4": (-15, 4.5),
    "a2": (-17, 5),
    "a7": (-18, 5.5),
    "a5": (-20, 6),

    # Extra
    "hd4": (15, -4.25),
    "hd2": (13, -3.75),
    "hd7": (12, -3.25),
    "hd5": (10, -2.75),
    "hd3": (8, -2.25),
    "hd1": (6, -1.75),
    "hd6": (5, -1.25),
    "N4": (3, -0.75),
    "N2": (1, -0.25),
    "N7": (0, 0.25),
    "N5": (-2, 0.75),
    "ha3": (-4, 1.25),
    "ha1": (-6, 1.75),
    "ha6": (-7, 2.25),
    "ha4": (-9, 2.75),
    "ha2": (-11, 3.25),
    "ha7": (-12, 3.75),
    "ha5": (-14, 4.25),
}

BASIC_PITCHES = {
    Letter.G: (6, -1.5),
    Letter.E: (4, -1),
    Letter.C: (2, -0.5),
    Letter.A: (0, 0),
    Letter.F: (-1, 0.5),
    Letter.D: (-3, 1),
    Letter.B: (-5, 1.5),
}
REFERENCE_OCTAVE = 5


class Interval(pythagoras.Interval):
    def monzo(self):
        basic, octaves = self.basic_part()
        twos, elevens = BASIC_INTERVALS[basic]
        twos += octaves
        twos += self.augmentations * AUGMENTED_INFLECTION[0]
        elevens += self.augmentations * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[0] = twos
        result[4] = elevens
        return result


class Pitch(pythagoras.Pitch):
    def monzo(self):
        twos, elevens = BASIC_PITCHES[self.letter]
        twos += self.octave - REFERENCE_OCTAVE
        twos += self.sharps * AUGMENTED_INFLECTION[0]
        elevens += self.sharps * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[0] = twos
        result[4] = elevens
        return result


items = list(BASIC_INTERVALS.items())
BASIC_INTERVALS = {}
for token, exponents in items:
    _, interval = Interval.parse(token)
    BASIC_INTERVALS[interval] = exponents


BASIC_CHORDS = {
    "O": (("P1", "M4", "m7"), (2,)),
    "u": (("P1", "m4", "m7"), (1, 2)),
}

EXTRA_CHORDS = {
    "oaug": ("P1", "M4", "M7"),
}


if __name__ == '__main__':
    from numpy import *
    by_cents = []
    for interval in BASIC_INTERVALS:
        m = interval.monzo()
        cents = (m[0] + m[4] * log(11)/log(2))*1200
        by_cents.append((cents, interval))
    by_cents.sort()
    for cents, interval in by_cents:
        print(interval, cents)

    JI = log(PRIMES)
    for arrow, inflection in INFLECTIONS.items():
        print(arrow, dot(JI, inflection)/log(2)*1200)
