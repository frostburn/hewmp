"""
Tools for reversing parsed notation back into a standard form.
In other words in combination with parsing translate relative intervals like M3- to ratio notation such as 5/4 or (absolute) pitch notation like C5#-
"""
from collections import Counter
from numpy import array, log, pi, maximum, isclose, around
from .color import monzo_to_color
from .monzo import PRIMES


# TODO: Parse monzos into classes and add tokenization methods instead
# TODO: Notate neutral intervals


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


def extract_root(pitch):
    """
    Try to extract an integer root from a non-integral pitch
    """
    for root in range(1, 101):
        if isclose(pitch*root, around(pitch*root)).all():
            return pitch*root, root
    raise ValueError("Failed to extract root from Non-integral pitch")


def tokenize_fraction(pitch, primes, *extra_indices):
    """
    Tokenize pitch monzo defined by the primes as a fraction p/q
    """
    numerator = 1
    denominator = 1
    derooted, root = extract_root(pitch[:len(primes)])
    for coord, prime in zip(derooted, primes):
        if coord != int(coord):
            raise ValueError("Non-integral monzo")
        coord = int(coord)
        if coord > 0:
            numerator *= prime**coord
        if coord < 0:
            denominator *= prime**(-coord)
    if root == 1:
        if denominator == 1:
            result = str(numerator)
        else:
            result = "{}/{}".format(numerator, denominator)
    else:
        result = "{}/{}/{}".format(numerator, denominator, root)
    return "{}{}".format(result, tokenize_extras(pitch, *extra_indices))


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
            exp_otonal = coord + o
            exp_utonal = u - coord
            if exp_otonal != int(exp_otonal) or exp_utonal != int(exp_utonal):
                raise ValueError("Non-integral monzo")
            num_otonal *= prime**int(exp_otonal)
            num_utonal *= prime**int(exp_utonal)
        otonal.append(num_otonal)
        utonal.append(num_utonal)

    if max(otonal) <= max(utonal):
        return ":".join(map(str, otonal))
    return ";".join(map(str, utonal))


def rindex(lst, value):
    lst = list(lst)
    return len(lst) - lst[::-1].index(value) - 1


def reverse_inflections(inflections, basis_indices=(0, 1)):
    result = []
    for arrow, comma in inflections.items():
        for index in range(len(comma)):
            if index in basis_indices:
                continue
            if abs(comma[index]) == 1:
                result.append((index, arrow, comma))
                break
        else:
            raise ValueError("Comma {!r} doesn't define a single prime step for arrow '{}'".format(comma, arrow))
    return result


def basis_and_arrows(pitch, inflections, basis_indices=(0, 1)):
    base0 = pitch[basis_indices[0]]
    base1 = pitch[basis_indices[1]]
    arrow_counts = Counter()
    for index, arrow, comma in inflections:
        direction = comma[index]
        if pitch[index]*direction > 0:
            count = pitch[index]*direction
            if count != int(count):
                raise ValueError("Non-integral prime component")
            arrow_counts[arrow] = int(count)
            base0 -= comma[basis_indices[0]]*count
            base1 -= comma[basis_indices[1]]*count

    if base0 == int(base0):
        base0 = int(base0)
    if base1 == int(base1):
        base1 = int(base1)

    return base0, base1, arrow_counts


def tokenize_arrows(arrow_counts):
    arrow_str = ""
    for arrow, count in arrow_counts.items():
        arrow_str += arrow
        if count != int(count):
            raise ValueError("Non-integral arrow count")
        if count > 1:
            arrow_str += str(int(count))

    return arrow_str


PYTHAGOREAN_QUALITIES = ("m", "m", "m", "m", "P", "P", "P", "M", "M", "M", "M")
PYTHAGOREAN_INDEX_P1 = 5


def tokenize_interval(pitch, inflections):
    """
    Tokenize (relative) pitch monzo using the inflections provided

    Assumes that the first two coordinates form the pythagorean basis
    """
    derooted = pitch
    derooted, root = extract_root(derooted)
    twos, threes, arrow_counts = basis_and_arrows(derooted, inflections)
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
            quality += "a"
            index -= 7

    value = 7*twos + 11*threes
    sign = "-" if value < 0 else ""
    value = abs(value) + 1

    root_str = ""
    if root != 1:
        root_str = "/{}".format(root)

    return "{}{}{}{}{}".format(sign, quality, value, arrow_str, root_str)


def tokenize_color_interval(pitch, *extra_indices):
    token = monzo_to_color(pitch[:len(PRIMES)])
    return "{}{}".format(token, tokenize_extras(pitch, *extra_indices))


LYDIAN = ("F", "C", "G", "D", "A", "E", "B")
LYDIAN_INDEX_A = 4
REFERENCE_OCTAVE = 4
LETTER_OCTAVES = {
    "F": -6,
    "C": -4,
    "G": -3,
    "D": -1,
    "A": 0,
    "E": 2,
    "B": 3,
}
SHARP_INFLECTION = (-11, 7)


def notate_pitch(pitch, inflections):
    """
    Calculate the letter, octave, sharps, flats and other arrows corresponding to a pitch monzo
    """
    twos, threes, arrow_counts = basis_and_arrows(pitch, inflections)
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


def tokenize_pitch(pitch, inflections):
    """
    Tokenize (absolute) pitch monzo using the inflections provided

    Assumes that the first two coordinates form the pythagorean basis
    """
    fractional_pitch = pitch - around(pitch)
    pitch = pitch - fractional_pitch
    letter, octave, arrow_counts = notate_pitch(pitch, inflections)
    accidental = "b" * arrow_counts.pop("b", 0) + "#" * arrow_counts.pop("#", 0) + "x" * arrow_counts.pop("x", 0)
    arrow_str = tokenize_arrows(arrow_counts)

    fractional_transposition = ""
    if fractional_pitch.any():
        fractional_transposition = "&" + tokenize_interval(fractional_pitch, inflections)

    return "{}{}{}{}{}".format(letter, octave, accidental, arrow_str, fractional_transposition)


def get_inflections():
    from .parser import DEFAULT_INFLECTIONS
    return reverse_inflections(DEFAULT_INFLECTIONS)


if __name__ == "__main__":
    import argparse
    from hewmp.parser import IntervalParser, E_INDEX, HZ_INDEX, RAD_INDEX
    from hewmp.smitonic import smitonic_tokenize_interval, SMITONIC_INFLECTIONS, smitonic_tokenize_pitch

    parser = argparse.ArgumentParser(description='Display the HEWMP notation for the given fraction')
    parser.add_argument('input', type=str)
    parser.add_argument('--absolute', action="store_true")
    parser.add_argument('--smitonic', action="store_true")
    parser.add_argument('--color', action="store_true")
    args = parser.parse_args()

    inflections = get_inflections()
    smitonic_inflections = reverse_inflections(SMITONIC_INFLECTIONS, basis_indices=(0, 4))
    pitch = IntervalParser().parse(args.input)[0]
    if args.absolute:
        if args.smitonic:
            print(smitonic_tokenize_pitch(pitch, smitonic_inflections, E_INDEX, HZ_INDEX, RAD_INDEX))
        elif args.color:
            raise NotImplementedError("Absolute color notation not implemented yet")
        else:
            print(tokenize_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX))
    else:
        if args.smitonic:
            print(smitonic_tokenize_interval(pitch, smitonic_inflections, E_INDEX, HZ_INDEX, RAD_INDEX))
        elif args.color:
            print(tokenize_color_interval(pitch, E_INDEX, HZ_INDEX, RAD_INDEX))
        else:
            print(tokenize_interval(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX))
