from numpy import log, isclose
from .monzo import PRIMES, Mapping, Pitch, Interval
from .pythagoras import Letter, Quality
from .pythagoras import Interval as PythInterval
from .pythagoras import Pitch as PythPitch
from .arrow import SignedArrow


JI = Mapping(log(PRIMES), 440)


def calculate_augmentation(period, generator, cardinality):
    augmented = Interval()
    diminished = Interval()
    for _ in range(cardinality):
        augmented = augmented + generator
        diminished = diminished - generator

    while JI.nats(augmented) > JI.nats(period):
        augmented = augmented - period
    while JI.nats(diminished) < 0:
         diminished = diminished + period

    major_direction = 1
    if JI.nats(diminished) < JI.nats(augmented):
        augmented = diminished
        major_direction = -1

    return augmented, major_direction


def erect_interval(period, generator, cardinality, augmented, major_direction):
    basic = [(Interval(), Quality("P"))]
    interval = Interval()
    quality = Quality("P")
    for i in range(cardinality-2):
        interval = interval + generator
        while JI.nats(interval) > JI.nats(period):
            interval = interval - period
        basic.append((interval, quality))
        if major_direction > 0:
            quality = Quality("M")
        else:
            quality = Quality("m")
    interval = -generator
    while JI.nats(interval) < 0:
        interval = interval + period
    basic.append((interval, Quality("P")))

    basic_intervals = {}

    class Result(PythInterval):
        def basic_part(self):
            periods = (self.interval_class - 1)//cardinality
            basic_class = self.interval_class - periods*cardinality
            return self.__class__(self.quality, basic_class), periods

        def monzo(self):
            basic, periods = self.basic_part()
            return (basic_intervals[basic] + periods * period + self.augmentations * augmented).monzo.vector

    basic.sort(key=lambda i:JI.nats(i[0]))
    for index, (interval, quality) in enumerate(basic):
        key = Result(quality, index + 1)
        basic_intervals[key] = interval
        if quality == Quality("P"):
            key = Result(Quality("a"), index + 1)
            basic_intervals[key] = interval + augmented
            key = Result(Quality("d"), index + 1)
            basic_intervals[key] = interval - augmented
            key = Result(Quality("ha"), index + 1)
            basic_intervals[key] = interval + augmented/2
            key = Result(Quality("hd"), index + 1)
            basic_intervals[key] = interval - augmented/2
        if quality == Quality("M"):
            key = Result(Quality("m"), index + 1)
            basic_intervals[key] = interval - augmented
            key = Result(Quality("a"), index + 1)
            basic_intervals[key] = interval + augmented
            key = Result(Quality("d"), index + 1)
            basic_intervals[key] = interval - 2*augmented
            key = Result(Quality("N"), index + 1)
            basic_intervals[key] = interval - augmented/2
            key = Result(Quality("ha"), index + 1)
            basic_intervals[key] = interval + augmented/2
            key = Result(Quality("hd"), index + 1)
            basic_intervals[key] = interval - 3*augmented/2
        if quality == Quality("m"):
            key = Result(Quality("M"), index + 1)
            basic_intervals[key] = interval + augmented
            key = Result(Quality("a"), index + 1)
            basic_intervals[key] = interval + 2*augmented
            key = Result(Quality("d"), index + 1)
            basic_intervals[key] = interval - augmented
            key = Result(Quality("N"), index + 1)
            basic_intervals[key] = interval + augmented/2
            key = Result(Quality("ha"), index + 1)
            basic_intervals[key] = interval + 3*augmented/2
            key = Result(Quality("hd"), index + 1)
            basic_intervals[key] = interval - augmented/2

    return Result


def erect_pitch(period, generator, cardinality, up, augmented, reference_octave=5):
    if up is None:
        up = cardinality // 2
    down = cardinality - up - 1

    scale = [Pitch()]
    interval = Interval()
    for _ in range(up):
        interval = interval + generator
        while JI.nats(interval) > JI.nats(period):
            interval = interval - period
        scale.append(Pitch() + interval)
    interval = Interval()
    for _ in range(down):
        interval = interval - generator
        while JI.nats(interval) < 0:
            interval = interval + period
        scale.append(Pitch() + interval)

    scale.sort(key=lambda p: JI.nats(p - Pitch()))

    basic_pitches = {}
    for letter, pitch in zip(Letter, scale):
        basic_pitches[letter] = pitch

    class Result(PythPitch):
        def monzo(self):
            return (basic_pitches[self.letter] + (self.octave - reference_octave) * period + self.sharps * augmented).monzo.vector

    return Result


def calculate_inflections(period, generator, cardinality):
    scale = [Interval()]
    up = Interval()
    down = Interval()
    for _ in range(cardinality):
        up = up + generator
        down = down - generator
        scale.extend([up, down])

    prime_inflections = {}
    for prime in PRIMES:
        target = Interval(SemiMonzo(Fraction(prime)))
        target_nats = JI.nats(target)
        best_error = float("inf")
        best = None
        for interval in scale:
            while JI.nats(interval) < target_nats:
                interval = interval + period
            while JI.nats(interval) > target_nats:
                interval = interval - period
            if abs(JI.nats(interval) - target_nats) < best_error:
                best_error = abs(JI.nats(interval) - target_nats)
                best = interval
            if abs(JI.nats(interval + period) - target_nats) < best_error:
                best_error = abs(JI.nats(interval + period) - target_nats)
                best = interval + period
        if JI.nats(best) < target_nats:
            prime_inflections[prime] = target - best
        else:
            prime_inflections[prime] = best - target

    inflections = {}
    two_three = []
    if not isclose(JI.nats(prime_inflections[2]), 0):
        two_three.append(prime_inflections[2])
    if not isclose(JI.nats(prime_inflections[3]), 0):
        two_three.append(prime_inflections[3])
    for prime, arrow in zip(PRIMES[2:], SignedArrow):
        inflection = prime_inflections[prime]
        if isclose(JI.nats(inflection), 0):
            inflection = two_three.pop()
        inflections[arrow] = inflection.monzo.vector

    return inflections


def erect_spine(period, generator, cardinality, up=None, reference_octave=5):
    augmented, major_direction = calculate_augmentation(period, generator, cardinality)
    intervalCls = erect_interval(period, generator, cardinality, augmented, major_direction)
    pitchCls = erect_pitch(period, generator, cardinality, up, augmented, reference_octave=reference_octave)
    inflections = calculate_inflections(period, generator, cardinality)
    return intervalCls, pitchCls, inflections


if __name__ == '__main__':
    import argparse
    from .parser import IntervalParser
    from .monzo import SemiMonzo
    from fractions import Fraction

    parser = argparse.ArgumentParser(description='Display information about the given spine')
    parser.add_argument('period', type=str)
    parser.add_argument('generator', type=str)
    parser.add_argument('cardinality', type=int)
    parser.add_argument('--up', type=int)
    parser.add_argument('--octave', type=int, default=5)
    parser.add_argument('--base-frequency', type=float, default=440.0)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    interval_parser = IntervalParser()
    period = interval_parser.parse(args.period).value()
    generator = interval_parser.parse(args.generator).value()

    cardinality = args.cardinality
    JI.base_frequency = args.base_frequency

    intervalCls, pitchCls, inflections = erect_spine(period, generator, cardinality, up=args.up, reference_octave=args.octave)

    mstr = lambda interval: " ".join([str(c) for c in interval.monzo()])

    def print_intervals(intervals):
        for cents, interval in intervals:
            print("{} {}{}".format(cents, interval.quality.value, interval.interval_class))
            if args.verbose:
                print(mstr(interval))

    print("Basic pitches")
    for letter in list(Letter)[:cardinality]:
        octave = 5
        pitch = pitchCls(letter, 0, octave)
        frequency = JI(Pitch(pitch.monzo()))
        print("{}Hz {}{}".format(frequency, letter.value, octave))
        if args.verbose:
            print(mstr(pitch))

    intervals = []
    for quality in [Quality("P"), Quality("m"), Quality("M")]:
        for interval_class in range(1, 1 + cardinality):
            try:
                interval = intervalCls(quality, interval_class)
                cents = JI.nats(Interval(interval.monzo())) / log(2) * 1200
                intervals.append((cents, interval))
            except KeyError:
                pass
    intervals.sort()
    print("Basic intervals")
    print_intervals(intervals)

    intervals = []
    for quality in [Quality("a"), Quality("d")]:
        for interval_class in range(1, 1 + cardinality):
            interval = intervalCls(quality, interval_class)
            cents = JI.nats(Interval(interval.monzo())) / log(2) * 1200
            intervals.append((cents, interval))
    intervals.sort()
    print("Augmented intervals")
    print_intervals(intervals)

    intervals = []
    for interval_class in range(1, 1 + cardinality):
        try:
            interval = intervalCls(Quality("N"), interval_class)
            cents = JI.nats(Interval(interval.monzo())) / log(2) * 1200
            intervals.append((cents, interval))
        except KeyError:
            pass
    intervals.sort()
    print("Neutral intervals")
    print_intervals(intervals)

    intervals = []
    for quality in [Quality("ha"), Quality("hd")]:
        for interval_class in range(1, 1 + cardinality):
            interval = intervalCls(quality, interval_class)
            cents = JI.nats(Interval(interval.monzo())) / log(2) * 1200
            intervals.append((cents, interval))
    intervals.sort()
    print("Half-augmented intervals")
    print_intervals(intervals)

    print("Inflections")
    inflections = calculate_inflections(period, generator, cardinality)
    for arrow, inflection in inflections.items():
        cents = JI.nats(Interval(SemiMonzo(inflection))) / log(2) * 1200
        print("{} {} {}".format(arrow.value, " ".join([str(c) for c in inflection]), cents))
