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


def mos_rhythm(num_onsets, generator, period=1):
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
    limit = 8
    show_variations = True
    seen = set()
    print("MOS rhythms")
    for period in range(2, limit+1):
        for generator in range(1, period+1):
            for num_onsets in range(1, period+1):
                td = mos_rhythm(num_onsets, generator, period)
                string = sequence_to_string(time_duration_to_sequence(td))
                if string in seen:
                    continue
                for _ in range(len(string)):
                    seen.add(string)
                    string = rotate_string(string)
                print("MOS({:2d},{:2d},{:2d}) =".format(num_onsets, generator, period), string)

    print("Euclidean rhythms")
    for i in range(2, limit+1):
        for j in range(1, i+1):
            sequence = euclidean_rhythm(j, i)
            string = sequence_to_string(sequence)
            print("E({:2d},{:2d}) =".format(j, i), string, "! "[string in seen])
            if show_variations:
                variations = set([string])
                for k in range(1, sum(sequence)):
                    variation = sequence_to_string(rotate_sequence(sequence, k))
                    if variation not in variations:
                        print(" {}: {}".format(k, variation))
                        variations.add(variation)
