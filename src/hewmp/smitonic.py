from numpy import array
from .chord_parser import separate_by_arrows

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
    "d": [-8, 0, 0, 0, 1, 0, 0, 0, 1],
    "U": [-10, 0, 0, 0, 1.5, 0, 0, 0, 0, 1],
    "D": [10, 0, 0, 0, -1.5, 0, 0, 0, 0, -1],
    "M": [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1],
    "W": [-5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
}

_PITCH_LENGTH = 14
for key, value in list(SMITONIC_INFLECTIONS.items()):
    SMITONIC_INFLECTIONS[key] = array(value + [0] * (_PITCH_LENGTH - len(value)))

SMITONIC_BASIC_INTERVALS = {
    "n6": (23, -6.5),
    "n4": (21, -6),
    "n2": (19, -5.5),
    "n7": (18, -5),
    "n5": (16, -4.5),
    "n3": (14, -4),
    "n1": (12, -3.5),
    "s6": (11, -3),
    "s4": (9, -2.5),
    "s2": (7, -2),
    "s7": (6, -1.5),
    "s5": (4, -1),
    "s3": (2, -0.5),
    # "P1": (0, 0),
    "L6": (-1, 0.5),
    "L4": (-3, 1),
    "L2": (-5, 1.5),
    "L7": (-6, 2),
    "L5": (-8, 2.5),
    "L3": (-10, 3),
    "W1": (-12, 3.5),
    "W6": (-13, 4),
    "W4": (-15, 4.5),
    "W2": (-17, 5),
    "W7": (-18, 5.5),
    "W5": (-20, 6),
    "W3": (-22, 6.5),
}

SMITONIC_WIDE_INFLECTION = (-12, 3.5)
SMITONIC_INTERVAL_QUALITIES = "nsLW"


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
# P - perfect
# So we use JKNOQRS
SMITONIC_BASIC_PITCHES = {
    "S": (5, -1.5),
    "Q": (3, -1),
    "N": (1, -0.5),
    "J": (0, 0),
    "R": (-2, 0.5),
    "O": (-4, 1),
    "K": (-5, 1.5),
}


def smitonic_parse_pitch(token, inflections):
    from .parser import REFERENCE_OCTAVE, zero_pitch

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

    result[0] += octave - REFERENCE_OCTAVE + basic_pitch[0]
    result[4] += basic_pitch[1]

    return result