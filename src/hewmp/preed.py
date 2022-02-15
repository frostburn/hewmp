from numpy import array, zeros
from .arrow import SignedArrow as SA
from .monzo import PRIMES
from .pythagoras import Quality, Letter
from . import pythagoras


# Notation inspired by the Breedsma


INFLECTIONS = {
    SA("+-"): [-2, 2, -0.5],
    SA("><"): [-0.75, 2.25, 0, -1],
    SA("^v"): [-0.5, 2.5, 0, 0, -1],
    SA("i!"): [4.5, -0.5, 0, 0, 0, -1],
    SA("*%"): [-2.5, -1, 0, 0, 0, 0, 1],
    SA("AV"): [-9, 3, 0, 0, 0, 0, 0, 1],
    SA("un"): [1.75, 1.75, 0, 0, 0, 0, 0, 0, -1],
    SA("UD"): [1.5, -4, 0, 0, 0, 0, 0, 0, 0, 1],
    SA("MW"): [1, 2.5, 0, 0, 0, 0, 0, 0, 0, 0, -1],
}

for key, value in list(INFLECTIONS.items()):
    INFLECTIONS[key] = array(value + [0] * (len(PRIMES) - len(value)))


class Interval(pythagoras.Interval):
    def monzo(self):
        return super().monzo() / 2

    @classmethod
    def from_monzo(cls, monzo, inflection=INFLECTIONS):
        counts = {}
        monzo = monzo + 0
        for i in range(2, len(PRIMES)):
            for arrow, inflection in INFLECTIONS.items():
                if inflection[i]:
                    break
            count = monzo[i] / inflection[i]
            counts[arrow] = count
            monzo -= count*inflection
        interval, sign = super().from_exponents(2*monzo[0], 2*monzo[1])
        return interval, sign, counts


class Pitch(pythagoras.Pitch):
    def monzo(self):
        return super().monzo() / 2

    # TODO: from_monzo


EXTRA_CHORDS = {
    "ph5":  ("P1", "a5-2", "M9"),
    "ph7":  ("P1", "a5-2", "M9", "ha12-"),
    "ph9":  ("P1", "a5-2", "M9", "ha12-", "M17"),
    "ph11": ("P1", "a5-2", "M9", "ha12-", "M17", "M21"),
    "ph13": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-"),
    "ph15": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2"),
    "ph17": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30"),
    "ph19": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33"),
    "ph21": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33", "ha34-"),
    "ph23": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33", "ha34-", "ha36"),
    "ph25": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33", "ha34-", "ha36", "aa37-4"),
    "ph27": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33", "ha34-", "ha36", "aa37-4", "a39"),
    "ph29": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33", "ha34-", "ha36", "aa37-4", "a39", "a40+2"),
    "ph31": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33", "ha34-", "ha36", "aa37-4", "a39", "a40+2", "M42-"),
    "ph33": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33", "ha34-", "ha36", "aa37-4", "a39", "a40+2", "M42-", "a43"),
    "ph35": ("P1", "a5-2", "M9", "ha12-", "M17", "M21", "P25-", "a27-2", "M30", "d33", "ha34-", "ha36", "aa37-4", "a39", "a40+2", "M42-", "a43", "haa44-3"),
}


if __name__ == '__main__':
    from numpy import *
    target = log(29/16/sqrt(2))/log(2)*1200
    by_error = []
    by_cents = []
    for interval in ["d1", "hd1", "ha1", "hd2", "m2", "M2", "m3", "M3", "P4", "a4", "d5", "P5", "ha5", "a5", "hd6", "m6", "M6", "m7", "M7"]:
        _, interval = Interval.parse(interval)
        m = interval.monzo()
        cents = (m[0] + m[1] * log(3)/log(2))*1200
        by_cents.append((cents, interval))
        by_error.append((abs(cents-target), interval))
    by_cents.sort()
    for cents, interval in by_cents:
        print(interval, cents)
    print("target", target)
    by_error.sort()
    for error, interval in by_error[:5]:
        print(error, interval)

    JI = log(PRIMES)/log(2)*1200
    for arrow, inflection in INFLECTIONS.items():
        print(arrow, dot(JI, inflection))

    print("5", log(5)/log(2)*1200, dot(JI, Interval.parse("a33")[1].monzo() - 2*INFLECTIONS[SA("+-")]))
    print("~7", log(7)/log(2)*1200, dot(JI, Interval.parse("ha40")[1].monzo() - INFLECTIONS[SA("+-")]))
    print("7", log(7)/log(2)*1200, dot(JI, Interval.parse("ha40")[1].monzo() - INFLECTIONS[SA("><")]))
    print("~11", log(11)/log(2)*1200, dot(JI, Interval.parse("M49")[1].monzo()))
    print("11", log(11)/log(2)*1200, dot(JI, Interval.parse("M49")[1].monzo() - INFLECTIONS[SA("^v")]))
    print("~31", log(31)/log(2)*1200, dot(JI, Interval.parse("M70")[1].monzo() - INFLECTIONS[SA("+-")]))
    print("31", log(31)/log(2)*1200, dot(JI, Interval.parse("M70")[1].monzo() - INFLECTIONS[SA("MW")]))

    print("--Associated Commas--")
    print("Breedsma", log(2401/2400)/log(2)*1200)
    print("Rastma", log(243/242)/log(2)*1200)
    print("(Telemann)", log(41067/40960)/log(2)*1200)
    print("septendecimal semitones comma", log(289/288)/log(2)*1200)
    print("Boethius' comma", log(513/512)/log(2)*1200)
    print("()", log(279936/279841)/log(2)*1200)
    print("()", log(43059200/43046721)/log(2)*1200)
    print("(DoReMi 31)", log(961/960)/log(2)*1200)
