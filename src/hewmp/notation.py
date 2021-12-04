"""
Tools for reversing parsed notation back into a standard form.
In other words in combination with parsing translate relative intervals like M3- to ratio notation such as 5/4 or (absolute) pitch notation like C5#-
"""
from collections import Counter
from numpy import array, log, pi, maximum


def tokenize_extras(pitch, e_index=None, hz_index=None, rad_index=None):
    """
    Tokenize extra bits like cents, Hz and phase offsets as transpositions
    """
    result = []
    if e_index is not None:
        nats = pitch[e_index]
        if nats != 0:
            result.append("{}c".format(nats*1200/log(2)))
    if hz_index is not None:
        hz = pitch[hz_index]
        if hz != 0:
            result.append("{}Hz".format(hz))
    if rad_index is not None:
        rads = pitch[rad_index]
        if rads != 0:
            result.append("{}deg".format(180*rads/pi))
    if result:
        return "&" + "&".join(result)
    return ""


def tokenize_fraction(pitch, primes, *extra_indices):
    """
    Tokenize pitch monzo defined by the primes as a fraction p/q
    """
    numerator = 1
    denominator = 1
    for coord, prime in zip(pitch, primes):
        if coord != int(coord):
            raise ValueError("Non-integral monzo")
        coord = int(coord)
        if coord > 0:
            numerator *= prime**coord
        if coord < 0:
            denominator *= prime**(-coord)
    if denominator == 1:
        return "{}{}".format(numerator, tokenize_extras(pitch, *extra_indices))
    return "{}/{}{}".format(numerator, denominator, tokenize_extras(pitch, *extra_indices))


def tokenize_otonal_utonal(pitches, primes):
    """
    Tokenize a chord like =M- in otonal (4:5:6) or utonal (15;12;10) notation depending on which one is simpler

    Assumes that there are no extra bits
    """
    if len(pitches) < 2:
        raise ValueError("Need at least two pitches to make a chord")
    otonal_root = -array(pitches[0])
    utonal_root = array(pitches[0])
    for pitch in pitches[1:]:
        otonal_root = maximum(otonal_root, -array(pitch))
        utonal_root = maximum(utonal_root, pitch)

    otonal = []
    utonal = []
    for pitch in pitches:
        num_otonal = 1
        num_utonal = 1
        for coord, prime, o, u in zip(pitch, primes, otonal_root, utonal_root):
            if coord != int(coord):
                raise ValueError("Non-integral monzo")
            num_otonal *= prime**int(coord + o)
            num_utonal *= prime**int(u - coord)
        otonal.append(num_otonal)
        utonal.append(num_utonal)

    if max(otonal) <= max(utonal):
        return ":".join(map(str, otonal))
    return ";".join(map(str, utonal))


def rindex(lst, value):
    lst = list(lst)
    return len(lst) - lst[::-1].index(value) - 1


def reverse_inflections(inflections):
    result = []
    for arrow, comma in inflections.items():
        index = 0
        if 1 in comma:
            index = rindex(comma, 1)
        if -1 in comma:
            index = max(index, rindex(comma, -1))
        result.append((index, arrow, comma))
    return result


def pythagoras_and_arrows(pitch, inflections):
    twos = pitch[0]
    threes = pitch[1]
    arrow_counts = Counter()
    for index, arrow, comma in inflections:
        direction = comma[index]
        if pitch[index]*direction > 0:
            count = pitch[index]*direction
            if count != int(count):
                raise ValueError("Non-integral monzo")
            arrow_counts[arrow] = int(count)
            twos -= comma[0]*count
            threes -= comma[1]*count

    if twos != int(twos) or threes != int(threes):
        raise ValueError("Non-integral monzo")

    twos = int(twos)
    threes = int(threes)

    return twos, threes, arrow_counts


def tokenize_arrows(arrow_counts):
    arrow_str = ""
    for arrow, count in arrow_counts.items():
        arrow_str += arrow
        if count != int(count):
            raise ValueError("Non-integral monzo")
        if count > 1:
            arrow_str += str(int(count))

    return arrow_str


PYTHAGOREAN_QUALITIES = ("m", "m", "m", "m", "P", "P", "P", "M", "M", "M", "M")
PYTHAGOREAN_INDEX_P1 = 5


def tokenize_interval(pitch, inflections, *extra_indices):
    """
    Tokenize (relative) pitch monzo using the inflections provided

    Assumes that the first two coordinates form the pythagorean basis
    """
    twos, threes, arrow_counts = pythagoras_and_arrows(pitch, inflections)
    arrow_str = tokenize_arrows(arrow_counts)

    index = threes + PYTHAGOREAN_INDEX_P1
    if index >= 0 and index < len(PYTHAGOREAN_QUALITIES):
        quality = PYTHAGOREAN_QUALITIES[index]
    elif index < 0:
        quality = ""
        while index < 0:
            quality += "d"
            index += 7
    else:
        index -= len(PYTHAGOREAN_QUALITIES)
        quality = ""
        while index >= 0:
            quality += "A"
            index -= 7

    value = 7*twos + 11*threes
    sign = "-" if value < 0 else ""
    value = abs(value) + 1

    return "{}{}{}{}{}".format(sign, quality, value, arrow_str, tokenize_extras(pitch, *extra_indices))


LYDIAN = ("F", "C", "G", "D", "a", "E", "B")
LYDIAN_INDEX_A = 4
REFERENCE_OCTAVE = 4
LETTER_OCTAVES = {
    "F": -6,
    "C": -4,
    "G": -3,
    "D": -1,
    "a": 0,
    "E": 2,
    "B": 3,
}
SHARP_INFLECTION = (-11, 7)


def notate_pitch(pitch, inflections):
    """
    Calculate the letter, octave, sharps, flats and other arrows corresponding to a pitch monzo
    """
    twos, threes, arrow_counts = pythagoras_and_arrows(pitch, inflections)
    index = threes + LYDIAN_INDEX_A
    letter = LYDIAN[index%len(LYDIAN)]
    while index < 0:
        arrow_counts["b"] += 1
        index += 7
        twos += SHARP_INFLECTION[0]
        threes += SHARP_INFLECTION[1]
    while index >= len(LYDIAN):
        if index >= 2*len(LYDIAN):
            arrow_counts["x"] += 1
            index -= 2*len(LYDIAN)
            twos -= 2*SHARP_INFLECTION[0]
            threes -= 2*SHARP_INFLECTION[1]
        else:
            arrow_counts["#"] += 1
            index -= len(LYDIAN)
            twos -= SHARP_INFLECTION[0]
            threes -= SHARP_INFLECTION[1]

    octave = REFERENCE_OCTAVE + twos + LETTER_OCTAVES[letter]

    return letter, octave, arrow_counts


def tokenize_pitch(pitch, inflections, *extra_indices):
    """
    Tokenize (absolute) pitch monzo using the inflections provided

    Assumes that the first two coordinates form the pythagorean basis
    """
    letter, octave, arrow_counts = notate_pitch(pitch, inflections)
    accidental = "b" * arrow_counts.pop("b", 0) + "#" * arrow_counts.pop("#", 0) + "x" * arrow_counts.pop("x", 0)
    arrow_str = tokenize_arrows(arrow_counts)

    return "{}{}{}{}{}".format(letter, octave, accidental, arrow_str, tokenize_extras(pitch, *extra_indices))


def get_inflections():
    from .parser import DEFAULT_INFLECTIONS
    return reverse_inflections(DEFAULT_INFLECTIONS)


if __name__ == "__main__":
    import argparse
    from hewmp_parser import parse_fraction, E_INDEX, HZ_INDEX, RAD_INDEX

    parser = argparse.ArgumentParser(description='Display the HEWMP notation for the given fraction')
    parser.add_argument('input', type=str)
    parser.add_argument('--absolute', action="store_true")
    args = parser.parse_args()

    inflections = get_inflections()
    pitch = parse_fraction(args.input)
    if args.absolute:
        print(tokenize_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX))
    else:
        print(tokenize_interval(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX))
