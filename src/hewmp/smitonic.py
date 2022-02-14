from numpy import array
from .chord_parser import separate_by_arrows
from .notation import basis_and_arrows, tokenize_arrows

SMITONIC_INFLECTIONS = {
    "+": [-4, 0, 1, 0, 0.5],
    "-": [4, 0, -1, 0, -0.5],
    ">": [8, 0, 0, -1, -1.5],
    "<": [-8, 0, 0, 1, 1.5],
    "^": [-5, 1, 0, 0, 1],
    "v": [5, -1, 0, 0, -1],
    "i": [2, 0, 0, 0, 0.5, -1],
    "!": [-2, 0, 0, 0, -0.5, 1],
    "*": [-11, 0, 0, 0, 2, 0, 1],
    "%": [11, 0, 0, 0, -2, 0, -1],
    "A": [6, 0, 0, 0, -0.5, 0, 0, -1],
    "V": [-6, 0, 0, 0, 0.5, 0, 0, 1],
    "u": [8, 0, 0, 0, -1, 0, 0, 0, -1],
    "n": [-8, 0, 0, 0, 1, 0, 0, 0, 1],
    "U": [-10, 0, 0, 0, 1.5, 0, 0, 0, 0, 1],
    "D": [10, 0, 0, 0, -1.5, 0, 0, 0, 0, -1],
    "M": [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1],
    "W": [-5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
}

_PITCH_LENGTH = 14
for key, value in list(SMITONIC_INFLECTIONS.items()):
    SMITONIC_INFLECTIONS[key] = array(value + [0] * (_PITCH_LENGTH - len(value)))

SMITONIC_BASIC_INTERVALS = {
    "n4": (21, -6),
    "n2": (19, -5.5),
    "n7": (18, -5),
    "n5": (16, -4.5),
    "n3": (14, -4),
    "n1": (12, -3.5),
    "n6": (11, -3),
    "s4": (9, -2.5),
    "s2": (7, -2),
    "s7": (6, -1.5),
    "s5": (4, -1),
    "p3": (2, -0.5),
    "p1": (0, 0),
    "p6": (-1, 0.5),
    "L4": (-3, 1),
    "L2": (-5, 1.5),
    "L7": (-6, 2),
    "L5": (-8, 2.5),
    "W3": (-10, 3),
    "W1": (-12, 3.5),
    "W6": (-13, 4),
    "W4": (-15, 4.5),
    "W2": (-17, 5),
    "W7": (-18, 5.5),
    "W5": (-20, 6),
}

SMITONIC_WIDE_INFLECTION = (-12, 3.5)
SMITONIC_INTERVAL_QUALITIES = "nspLW"


def smitonic_parse_arrows(token, inflections):
    from .parser import zero_pitch

    quality = token[0]
    token = token[1:]
    wide = 0
    while token[0] == "W":
        wide += 1
        token = token[1:]
    while token[0] == "n":
        wide -= 1
        token = token[1:]

    result = zero_pitch()
    result[0] += SMITONIC_WIDE_INFLECTION[0] * wide
    result[4] += SMITONIC_WIDE_INFLECTION[1] * wide

    separated = separate_by_arrows(token)

    for arrow_token in separated[1:]:
        arrows = 1
        if len(arrow_token) > 1:
            arrows = int(arrow_token[1:])
        result += inflections[arrow_token[0]]*arrows

    interval_class = int(separated[0])
    octave = (interval_class - 1)//7
    basic_class = interval_class - octave*7
    lookup = "{}{}".format(quality, basic_class)
    basic_pitch = SMITONIC_BASIC_INTERVALS[lookup]

    result[0] += octave + basic_pitch[0]
    result[4] += basic_pitch[1]

    return result


# We'd like to use JKLMNOP, but
# the following are reserved by something more important:
# L - large
# M - major
# N - neutral
# P - perfect
# T - timestamp
# R - repeat last pattern
# So we use JKOQSUY
SMITONIC_BASIC_PITCHES = {
    "Y": (6, -1.5),
    "S": (4, -1),
    "O": (2, -0.5),
    "J": (0, 0),
    "U": (-1, 0.5),
    "Q": (-3, 1),
    "K": (-5, 1.5),
}
SMITONIC_REFERENCE_OCTAVE = 5


def smitonic_parse_pitch(token, inflections):
    from .parser import zero_pitch

    letter = token[0]
    token = token[1:]
    if token and token[0] == "-":
        octave_token = token[0]
        token = token[1:]
    else:
        octave_token = ""
    while token and token[0].isdigit():
        octave_token += token[0]
        token = token[1:]
    octave = int(octave_token)
    sharp = 0
    while token and token[0] == "#":
        sharp += 1
        token = token[1:]
    while token and token[0] == "x":
        sharp += 2
        token = token[1:]
    while token and token[0] == "b":
        sharp -= 1
        token = token[1:]


    result = zero_pitch()
    result[0] += SMITONIC_WIDE_INFLECTION[0] * sharp
    result[4] += SMITONIC_WIDE_INFLECTION[1] * sharp

    separated = separate_by_arrows(token)

    for arrow_token in separated[1:]:
        arrows = 1
        if len(arrow_token) > 1:
            arrows = int(arrow_token[1:])
        result += inflections[arrow_token[0]]*arrows

    basic_pitch = SMITONIC_BASIC_PITCHES[letter]

    result[0] += octave - SMITONIC_REFERENCE_OCTAVE + basic_pitch[0]
    result[4] += basic_pitch[1]

    return result


SMITONIC_QUALITIES = ("s", "s", "s", "s", "p", "p", "p", "L", "L", "L", "L")
SMITONIC_INDEX_P1 = 5


def smitonic_tokenize_interval(pitch, inflections):
    """
    Tokenize (relative) pitch monzo using the inflections provided
    """
    twos, elevens, arrow_counts = basis_and_arrows(pitch, inflections, basis_indices=(0, 4))
    arrow_str = tokenize_arrows(arrow_counts)

    index = int(2*elevens + SMITONIC_INDEX_P1)
    if index >= 0 and index < len(SMITONIC_QUALITIES):
        quality = SMITONIC_QUALITIES[index]
    elif index < 0:
        quality = ""
        while index < 0:
            quality += "n"
            index += 7
    else:
        index -= len(SMITONIC_QUALITIES)
        quality = ""
        while index >= 0:
            quality += "W"
            index -= 7

    value = int(7*twos + 24*elevens)
    sign = "-" if value < 0 else ""
    value = abs(value) + 1

    return "{}{}{}{}".format(sign, quality, value, arrow_str)


NEREVARINE = ("Y", "S", "O", "J", "U", "Q", "K")
NEREVARINE_INDEX_J = 3
SMITONIC_LETTER_OCTAVES = {
    "Y": -6,
    "S": -4,
    "O": -2,
    "J": 0,
    "U": 1,
    "Q": 3,
    "K": 5,
}


def smitonic_notate_pitch(pitch, inflections):
    """
    Calculate the letter, octave, sharps, flats and other arrows corresponding to a pitch monzo
    """
    twos, elevens, arrow_counts = basis_and_arrows(pitch, inflections, basis_indices=(0, 4))
    index = int(2*elevens + NEREVARINE_INDEX_J)
    letter = NEREVARINE[index%len(NEREVARINE)]
    while index < 0:
        arrow_counts["b"] += 1
        index += 7
        twos += SMITONIC_WIDE_INFLECTION[0]
        elevens += SMITONIC_WIDE_INFLECTION[1]
    while index >= len(NEREVARINE):
        if index >= 2*len(NEREVARINE):
            arrow_counts["x"] += 1
            index -= 2*len(NEREVARINE)
            twos -= 2*SMITONIC_WIDE_INFLECTION[0]
            elevens -= 2*SMITONIC_WIDE_INFLECTION[1]
        else:
            arrow_counts["#"] += 1
            index -= len(NEREVARINE)
            twos -= SMITONIC_WIDE_INFLECTION[0]
            elevens -= SMITONIC_WIDE_INFLECTION[1]

    octave = SMITONIC_REFERENCE_OCTAVE + twos + SMITONIC_LETTER_OCTAVES[letter]

    return letter, octave, arrow_counts


def smitonic_tokenize_pitch(pitch, inflections):
    """
    Tokenize (absolute) pitch monzo using the inflections provided
    """
    letter, octave, arrow_counts = smitonic_notate_pitch(pitch, inflections)
    accidental = "b" * arrow_counts.pop("b", 0) + "#" * arrow_counts.pop("#", 0) + "x" * arrow_counts.pop("x", 0)
    arrow_str = tokenize_arrows(arrow_counts)

    return "{}{}{}{}".format(letter, octave, accidental, arrow_str)


SMITONIC_BASIC_CHORDS = {
    "O": (("p1", "L4", "s7"), (2,)),
    "u": (("p1", "s4", "s7"), (1, 2)),
}

SMITONIC_EXTRA_CHORDS = {
    "smaug": ("p1", "L4", "L7"),
}
