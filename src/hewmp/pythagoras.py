# coding: utf-8

def read_number(token):
    if token and token[0] in "-+":
        num = token[0]
        token = token[1:]
    else:
        num = ""
    while token and token[0].isdigit():
        num += token[0]
        token = token[1:]
    if num:
        return token, int(num)
    return token, None


AUGMENTED_INFLECTION = (-11, 7)

BASIC_INTERVALS = {
    "d2": (19, -12),
    "d6": (18, -11),
    "d3": (16, -10),
    "d7": (15, -9),
    "d4": (13, -8),
    "d1": (11, -7),
    "d5": (10, -6),
    "m2": (8, -5),
    "m6": (7, -4),
    "m3": (5, -3),
    "m7": (4, -2),
    "P4": (2, -1),
    "P1": (0, 0),
    "P5": (-1, 1),
    "M2": (-3, 2),
    "M6": (-4, 3),
    "M3": (-6, 4),
    "M7": (-7, 5),
    "a4": (-9, 6),
    "a1": (-11, 7),
    "a5": (-12, 8),
    "a2": (-14, 9),
    "a6": (-15, 10),
    "a3": (-17, 11),
    "a7": (-18, 12),

    # Extra half-diminished intervals
    "hd2": (13.5, -8.5),
    "hd6": (12.5, -7.5),
    "hd3": (10.5, -6.5),
    "hd7": (9.5, -5.5),
    "hd4": (7.5, -4.5),
    "hd1": (5.5, -3.5),
    "hd5": (4.5, -2.5),
    # Extra neutral intervals
    "N2": (2.5, -1.5),
    "N6": (1.5, -0.5),
    "N3": (-0.5, 0.5),
    "N7": (-1.5, 1.5),
    # Extra half-augmented intervals
    "ha4": (-3.5, 2.5),
    "ha1": (-5.5, 3.5),
    "ha5": (-6.5, 4.5),
    "ha6": (-9.5, 6.5),
    "ha3": (-11.5, 7.5),
    "ha7": (-12.5, 8.5),
}


INTERVAL_QUALITIES = "dmPNMha"


def parse_interval(token):
    quality = token[0]
    token = token[1:]
    if quality == "h":
        quality += token[0]
        token = token[1:]
    augmented = 0
    while token[0] == "a":
        augmented += 1
        token = token[1:]
    while token[0] == "d":
        augmented -= 1
        token = token[1:]

    result = [0, 0]
    result[0] += AUGMENTED_INFLECTION[0] * augmented
    result[1] += AUGMENTED_INFLECTION[1] * augmented

    token, interval_class = read_number(token)
    octave = (interval_class - 1)//7
    basic_class = interval_class - octave*7
    lookup = "{}{}".format(quality, basic_class)
    basic_interval = BASIC_INTERVALS[lookup]

    result[0] += octave + basic_interval[0]
    result[1] += basic_interval[1]

    return token, result


BASIC_PITCHES = {
    "F": (6, -4),
    "C": (4, -3),
    "G": (3, -2),
    "D": (1, -1),
    "A": (0, 0),
    "E": (-2, 1),
    "B": (-3, 2),
}
REFERENCE_OCTAVE = 4


def parse_pitch(token):
    letter = token[0]
    token = token[1:]
    token, octave = read_number(token)
    sharp = 0
    while token and token[0] == "♮":
        token = token[1:]
    while token and token[0] in "#♯":
        sharp += 1
        token = token[1:]
    while token and token[0] in "x𝄪":
        sharp += 2
        token = token[1:]
    while token and token[0] in "b♭":
        sharp -= 1
        token = token[1:]
    while token and token[0] == "𝄫":
        sharp -= 2
        token = token[1:]

    while token and token[0] in "t𝄲":
        sharp += 0.5
        token = token[1:]
    while token and token[0] in "d𝄳":
        sharp -= 0.5
        token = token[1:]

    result = [0, 0]
    result[0] += AUGMENTED_INFLECTION[0] * sharp
    result[1] += AUGMENTED_INFLECTION[1] * sharp

    if octave is None:
        token, octave = read_number(token)

    basic_pitch = BASIC_PITCHES[letter]

    result[0] += octave - REFERENCE_OCTAVE + basic_pitch[0]
    result[1] += basic_pitch[1]

    return token, result
