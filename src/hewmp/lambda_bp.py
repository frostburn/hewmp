from numpy import array, zeros
from .arrow import SignedArrow as SA
from .monzo import PRIMES
from .pythagoras import Quality, Letter
from . import pythagoras


AUGMENTED_INFLECTION = (16, -9)


INFLECTIONS = {
    SA("+-"): [0, -5, 1, 2],
    SA("><"): [1, 10, 0, -6],
    SA("^v"): [0, 12, 0, -8, 1],
    SA("i!"): [0, 3, 0, -3, 0, 1],
    SA("*%"): [0, 1, 0, -2, 0, 0, 1],
    SA("AV"): [0, 8, 0, -3, 0, 0, 0, -1],
    SA("un"): [0, -6, 0, 5, 0, 0, 0, 0, -1],
    SA("UD"): [0, -4, 0, 4, 0, 0, 0, 0, 0, -1],
    SA("MW"): [0, 12, 0, -5, 0, 0, 0, 0, 0, 0, -1],
}

for key, value in list(INFLECTIONS.items()):
    INFLECTIONS[key] = array(value + [0] * (len(PRIMES) - len(value)))


BASIC_INTERVALS = {
    "d5": (-28, 16),
    "d7": (-26, 15),
    "d9": (-24, 14),
    "d2": (-23, 13),
    "d4": (-21, 12),
    "d6": (-19, 11),
    "d8": (-17, 10),
    "d1": (-16, 9),
    "d3": (-14, 8),
    "m5": (-12, 7),
    "m7": (-10, 6),
    "m9": (-8, 5),
    "m2": (-7, 4),
    "m4": (-5, 3),
    "m6": (-3, 2),
    "P8": (-1, 1),
    "P1": (0, 0),
    "P3": (2, -1),
    "M5": (4, -2),
    "M7": (6, -3),
    "M9": (8, -4),
    "M2": (9, -5),
    "M4": (11, -6),
    "M6": (13, -7),
    "a8": (15, -8),
    "a1": (16, -9),
    "a3": (18, -10),
    "a5": (20, -11),
    "a7": (22, -12),
    "a9": (24, -13),
    "a2": (25, -14),
    "a4": (27, -15),
    "a6": (29, -16),

    # Extra
    "hd5": (-20, 11.5),
    "hd7": (-18, 10.5),
    "hd9": (-16, 9.5),
    "hd2": (-15, 8.5),
    "hd4": (-13, 7.5),
    "hd6": (-11, 6.5),
    "hd8": (-9, 5.5),
    "hd1": (-8, 4.5),
    "hd3": (-5, 3.5),
    "N5": (-4, 2.5),
    "N7": (-2, 1.5),
    "N9": (0, 0.5),
    "N2": (1, -0.5),
    "N4": (3, -1.5),
    "N6": (5, -2.5),
    "ha8": (7, -3.5),
    "ha1": (8, -4.5),
    "ha3": (10, -5.5),
    "ha5": (12, -6.5),
    "ha7": (14, -7.5),
    "ha9": (16, -8.5),
    "ha2": (17, -9.5),
    "ha4": (19, -10.5),
    "ha6": (21, -11.5),
}

BASIC_PITCHES = {
    Letter.F: (-4, 2),
    Letter.H: (-2, 1),
    Letter.A: (0, 0),
    Letter.C: (1, -1),
    Letter.E: (3, -2),
    Letter.G: (5, -3),
    Letter.J: (7, -4),
    Letter.B: (9, -5),
    Letter.D: (10, -6),
}
REFERENCE_OCTAVE = 4


class Interval(pythagoras.Interval):
    def basic_part(self):
        tritaves = (self.interval_class - 1)//9
        basic_class = self.interval_class - tritaves*9
        return self.__class__(self.quality, basic_class), tritaves

    def monzo(self):
        basic, tritaves = self.basic_part()
        threes, sevens = BASIC_INTERVALS[basic]
        threes += tritaves
        threes += self.augmentations * AUGMENTED_INFLECTION[0]
        sevens += self.augmentations * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[1] = threes
        result[3] = sevens
        return result


class Pitch(pythagoras.Pitch):
    def monzo(self):
        threes, sevens = BASIC_PITCHES[self.letter]
        threes += self.octave - REFERENCE_OCTAVE
        threes += self.sharps * AUGMENTED_INFLECTION[0]
        sevens += self.sharps * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[1] = threes
        result[3] = sevens
        return result


items = list(BASIC_INTERVALS.items())
BASIC_INTERVALS = {}
for token, exponents in items:
    _, interval = Interval.parse(token)
    BASIC_INTERVALS[interval] = exponents


BASIC_CHORDS = {}

EXTRA_CHORDS = {}


if __name__ == '__main__':
    from numpy import *
    target = log(31/27)/log(2)*1200
    by_error = []
    by_cents = []
    for interval in BASIC_INTERVALS:
        m = interval.monzo()
        cents = (m[1]*log(3) + m[3]*log(7))/log(2)*1200
        by_cents.append((cents, interval))
        by_error.append((abs(cents-target), interval))
    print("period", log(3)/log(2)*1200)
    by_cents.sort()
    for cents, interval in by_cents:
        print(interval, cents)
    print("target", target)
    by_error.sort()
    for error, interval in by_error[:3]:
        print(error, interval)

    JI = log(PRIMES)
    for arrow, inflection in INFLECTIONS.items():
        print(arrow, dot(JI, inflection)/log(2)*1200)
