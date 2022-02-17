from fractions import Fraction
from numpy import diff


def _bjorklund(subsequences):
    """
    Distribute onsets as evenly as possible by modifying subsequences
    """
    while True:
        remainder = subsequences[-1]
        distributed = []
        while subsequences and subsequences[-1] == remainder:
            distributed.append(subsequences.pop())
        if not subsequences or len(distributed) <= 1:
            subsequences.extend(distributed)
            return subsequences
        for i in range(min(len(distributed), len(subsequences))):
            subsequences[i].extend(distributed.pop())
        subsequences.extend(distributed)


def euclidean_rhythm(num_onsets, num_beats):
    """
    Evenly distributes a given number of onsets in a grid of the given size
    """
    sequence = [True] * num_onsets + [False] * (num_beats - num_onsets)
    return sum(_bjorklund([[b] for b in sequence]), [])


def _rotate_sequence(sequence):
    return sequence[1:] + sequence[:1]


def rotate_sequence(sequence, num_iter):
    if not any(sequence):
        return sequence
    for _ in range(num_iter):
        sequence = _rotate_sequence(sequence)
        while not sequence[0]:
            sequence = _rotate_sequence(sequence)
    return sequence


def sequence_to_time_duration(sequence):
    result = []
    time = None
    duration = 0
    for i, b in enumerate(sequence):
        if b:
            if time is not None:
                result.append((time, duration))
            duration = 0
            time = i
        duration += 1
    result.append((time, duration))
    return result


def time_duration_to_sequence(times_durations):
    end_time = 0
    for t, d in times_durations:
        end_time = max(end_time, t + d)
    sequence = [False] * end_time
    for t, _ in times_durations:
        sequence[t] = True
    return sequence


def sequence_to_string(sequence):
    return "".join([".x"[int(b)] for b in sequence])


def rotate_string(string):
    return string[-1] + string[:-1]


def pergen_rhythm(num_onsets, generator, period=1):
    beats = sorted([(generator * i) % period for i in range(num_onsets)] + [period])
    times = beats[:num_onsets]
    durations = diff(beats)
    return list(zip(times, durations))


def concatenated_geometric_rhythm(num_onsets, initial, factor):
    """
    Concatenated geometric progression
    """
    time = 0
    duration = initial
    result = []
    for _ in range(num_onsets):
        result.append((time, duration))
        time += duration
        duration *= factor
    return result


def concatenated_arithmetic_rhythm(num_onsets, initial, delta):
    """
    Concatenated arithmetic progression
    """
    time = 0
    duration = initial
    result = []
    for _ in range(num_onsets):
        result.append((time, duration))
        time += duration
        duration += delta
        if duration < 0:
            raise ValueError("Negative durations produced with delta = {}".format(delta))
    return result


def concatenated_harmonic_rhythm(num_onsets, initial, delta):
    """
    Concatenated harmonic progression
    """
    time = Fraction(0)
    result = []
    for n in range(num_onsets):
        duration = Fraction(1, initial + n*delta)
        if duration < 0:
            raise ValueError("Negative durations produced with delta = {}".format(delta))
        result.append((time, duration))
        time += duration
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Display rhythm patterns')
    parser.add_argument('limit', type=int)
    parser.add_argument('family', choices=["PG", "E"])
    parser.add_argument('--variations', action='store_true')
    args = parser.parse_args()

    if args.family == "PG":
        seen = set()
        print("Pergen Rhythms")
        for period in range(2, args.limit+1):
            for generator in range(1, period+1):
                for num_onsets in range(1, period+1):
                    td = pergen_rhythm(num_onsets, generator, period)
                    string = sequence_to_string(time_duration_to_sequence(td))
                    if string in seen:
                        continue
                    for _ in range(len(string)):
                        seen.add(string)
                        string = rotate_string(string)
                    for i in range(2, 10):
                        s = string.replace(".", "y" * i)
                        s = s.replace("x", "x" + "." * (i-1))
                        s = s.replace("y", ".")
                        for _ in range(len(s)):
                            seen.add(s)
                            s = rotate_string(s)
                    mos = "{}PG{}".format(generator, period)
                    x = "x{}".format(num_onsets)
                    print("[{} {}] =".format(x.ljust(3), mos.center(5)), string)
    else:
        print("Euclidean Rhythms")
        for i in range(2, args.limit+1):
            for j in range(1, i+1):
                sequence = euclidean_rhythm(j, i)
                string = sequence_to_string(sequence)
                euclid = "E{}".format(i)
                x = "x{}".format(j)
                print("[{} {}] =".format(x.ljust(3), euclid.center(3)), string)
                if args.variations:
                    variations = set([string])
                    for k in range(1, sum(sequence)):
                        variation = sequence_to_string(rotate_sequence(sequence, k))
                        if variation not in variations:
                            euclid = "{}E{}".format(k, i)
                            print(" [{} {}] =".format(x.ljust(3), euclid.center(5)), variation)
                            variations.add(variation)
