# coding: utf-8
AUGMENTED_INFLECTION = (-11, 7)

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

    while token and token[0] == "s":
        sharp += 0.5
        token = token[1:]
    while token and token[0] == "f":
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
