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


def exponential_rhythm(num_onsets, factor):
    time = 0
    duration = 1
    result = []
    for _ in range(num_onsets):
        result.append((time, duration))
        time += duration
        duration *= factor
    return result


if __name__ == "__main__":
    seen = set()
    print("MOS rhythms")
    for period in range(2, 17):
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
    for i in range(2, 17):
        for j in range(1, i+1):
            string = sequence_to_string(euclidean_rhythm(j, i))
            print("E({:2d},{:2d}) =".format(j, i), string, "! "[string in seen])