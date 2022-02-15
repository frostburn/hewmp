from numpy import array, zeros
from .arrow import SignedArrow as SA
from .monzo import PRIMES
from .pythagoras import Quality, Letter
from . import pythagoras


AUGMENTED_INFLECTION = (4, -2.5)


INFLECTIONS = {
    SA("+-"): [-4, 4, -1],
    SA("><"): [-2, -0.5, 0, 1],
    SA("^v"): [-9, 3.5, 0, 0, 1],
    SA("i!"): [-5, 5.5, 0, 0, 0, -1],
    # SA("i!"): [-10, 4, 0, 0, 0, 1],  # Also an option, but doesn't combine nicely with the syntonic +-
    SA("*%"): [-8, 2.5, 0, 0, 0, 0, 1],
    # SA("*%"): [-3, 4.5, 0, 0, 0, 0, -1],  # Also an option
    SA("AV"): [-9, 3, 0, 0, 0, 0, 0, 1],
    SA("un"): [-1, 3.5, 0, 0, 0, 0, 0, 0, -1],
    SA("UD"): [12, -4.5, 0, 0, 0, 0, 0, 0, 0, -1],
    SA("MW"): [1, 2.5, 0, 0, 0, 0, 0, 0, 0, 0, -1],
}

for key, value in list(INFLECTIONS.items()):
    INFLECTIONS[key] = array(value + [0] * (len(PRIMES) - len(value)))


BASIC_INTERVALS = {
    "d2": (-7, 4.5),
    "d3": (-6, 4),
    "d4": (-5, 3.5),
    "d5": (-4, 3),
    "d1": (-4, 2.5),
    "m2": (-3, 2),
    "m3": (-2, 1.5),
    "m4": (-1, 1),
    "m5": (0, 0.5),
    "P1": (0, 0),
    "M2": (1, -0.5),
    "M3": (2, -1),
    "M4": (3, -1.5),
    "M5": (4, -2),
    "a1": (4, -2.5),
    "a2": (5, -3),
    "a3": (6, -3.5),
    "a4": (7, -4),
    "a5": (8, -4.5),

    # Extra
    "hd2": (-5, 3.25),
    "hd3": (-4, 2.75),
    "hd4": (-3, 2.25),
    "hd5": (-2, 1.75),
    "hd1": (-2, 1.25),
    "N2": (-1, 0.75),
    "N3": (0, 0.25),
    "N4": (1, -0.25),
    "N5": (2, -0.75),
    "ha1": (2, -1.25),
    "ha2": (3, -1.75),
    "ha3": (4, -2.25),
    "ha4": (5, -2.75),
    "ha5": (6, -3.25),
}


BASIC_PITCHES = {
    Letter.J: (4, -2),
    Letter.G: (3, -1.5),
    Letter.E: (2, -1),
    Letter.C: (1, -0.5),
    Letter.A: (0, 0),
    Letter.H: (0, 0.5),
    Letter.F: (-1, 1),
    Letter.D: (-2, 1.5),
    Letter.B: (-3, 2),
}
REFERENCE_OCTAVE = 5


class Interval(pythagoras.Interval):
    def basic_part(self):
        octaves = (self.interval_class - 1)//5
        basic_class = self.interval_class - octaves*5
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


class Pitch(pythagoras.Pitch):
    def monzo(self):
        twos, threes = BASIC_PITCHES[self.letter]
        twos += self.octave - REFERENCE_OCTAVE
        twos += self.sharps * AUGMENTED_INFLECTION[0]
        threes += self.sharps * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[0] = twos
        result[1] = threes
        return result


items = list(BASIC_INTERVALS.items())
BASIC_INTERVALS = {}
for token, exponents in items:
    _, interval = Interval.parse(token)
    BASIC_INTERVALS[interval] = exponents


BASIC_CHORDS = {
    "m3": (("P1", "m3", "m4"), (1,)),
    "d6": (("P1", "m3", "m4", "d6"), (1, 3)),
    "M2": (("P1", "M2", "m4"), (1,)),
    "m5": (("P1", "M2", "m4", "m5"), (1, 3)),
}

EXTRA_CHORDS = {
    "semaphore": ("P1", "M2", "M3"),
    "sp3": ["P1", "M2", "M3"],
    "sp4": ["P1", "M2", "M3", "M4"],
    "sp5": ["P1", "M2", "M3", "M4", "M5"],
    "sp6": ["P1", "M2", "M3", "M4", "M5", "a6"],
    "sp7": ["P1", "M2", "M3", "M4", "M5", "a6", "a7"],
    "sp8": ["P1", "M2", "M3", "M4", "M5", "a6", "a7", "a8"],
    "sp9": ["P1", "M2", "M3", "M4", "M5", "a6", "a7", "a8", "a9"],
    "sp10": ["P1", "M2", "M3", "M4", "M5", "a6", "a7", "a8", "a9", "a10"],
}


if __name__ == '__main__':
    from numpy import *
    target = log(5/4)/log(2)*1200
    by_error = []
    by_cents = []
    for interval in BASIC_INTERVALS:
        m = interval.monzo()
        cents = (m[0] + m[1] * log(3)/log(2))*1200
        by_cents.append((cents, interval))
        by_error.append((abs(cents-target), interval))
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
