from numpy import array, zeros
from .arrow import SignedArrow as SA
from .monzo import PRIMES
from .pythagoras import Quality, Letter
from . import pythagoras


AUGMENTED_INFLECTION = (14, -6)


INFLECTIONS = {
    SA("+-"): [-10, -1, 5],
    SA("><"): [-12, 0, 4, 1],
    SA("^v"): [-22, 0, 8, 0, 1],
    SA("i!"): [-6, 0, 1, 0, 0, 1],
    SA("*%"): [-18, 0, 6, 0, 0, 0, 1],
    SA("AV"): [2, 0, 1, 0, 0, 0, 0, -1],
    SA("un"): [-14, 0, 8, 0, 0, 0, 0, 0, -1],
    SA("UD"): [-16, 0, 9, 0, 0, 0, 0, 0, 0, -1],
    SA("MW"): [-2, 0, 3, 0, 0, 0, 0, 0, 0, 0, -1],
}

for key, value in list(INFLECTIONS.items()):
    INFLECTIONS[key] = array(value + [0] * (len(PRIMES) - len(value)))


BASIC_INTERVALS = {
    "a3": (24, -10),
    "a4": (22, -9),
    "a5": (20, -8),
    "a6": (18, -7),
    "a1": (14, -6),
    "a2": (12, -5),
    "M3": (10, -4),
    "M4": (8, -3),
    "M5": (6, -2),
    "P6": (4, -1),
    "P1": (0, 0),
    "P2": (-2, 1),
    "m3": (-4, 2),
    "m4": (-6, 3),
    "m5": (-8, 4),
    "d6": (-10, 5),
    "d1": (-14, 6),
    "d2": (-16, 7),
    "d3": (-18, 8),
    "d4": (-20, 9),
    "d5": (-22, 10),

    # TODO: Neutral intervals
}

BASIC_PITCHES = {
    Letter.E: (8, -3),
    Letter.F: (6, -2),
    Letter.G: (4, -1),
    Letter.A: (0, 0),
    Letter.B: (-2, 1),
    Letter.C: (-4, 2),
    Letter.D: (-6, 3),
}
REFERENCE_OCTAVE = 4


class Interval(pythagoras.Interval):
    def monzo(self):
        basic, double_octaves = self.basic_part()
        twos, fives = BASIC_INTERVALS[basic]
        twos += 2*double_octaves
        twos += self.augmentations * AUGMENTED_INFLECTION[0]
        fives += self.augmentations * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[0] = twos
        result[2] = fives
        return result


class Pitch(pythagoras.Pitch):
    def monzo(self):
        twos, fives = BASIC_PITCHES[self.letter]
        twos += 2*(self.octave - REFERENCE_OCTAVE)
        twos += self.sharps * AUGMENTED_INFLECTION[0]
        fives += self.sharps * AUGMENTED_INFLECTION[1]
        result = zeros(len(PRIMES))
        result[0] = twos
        result[2] = fives
        return result


items = list(BASIC_INTERVALS.items())
BASIC_INTERVALS = {}
for token, exponents in items:
    _, interval = Interval.parse(token)
    BASIC_INTERVALS[interval] = exponents


BASIC_CHORDS = {
    "Mr": (("P1", "a2", "M3"), (1, 2)),
    "mr": (("P1", "P2", "M3"), (2,)),
}

EXTRA_CHORDS = {}


if __name__ == '__main__':
    from numpy import *
    target = log(31/16)/log(2)*1200
    by_error = []
    by_cents = []
    for interval in BASIC_INTERVALS:
        m = interval.monzo()
        cents = (m[0] + m[2] * log(5)/log(2))*1200
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
