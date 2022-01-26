# coding: utf-8
from numpy import dot, zeros, sign, array


PSEUDO_EDO_MAPPING = (7, 11, 16, 20, 24, 26, 29, 30, 32, 34, 37)
WA_COMMA = (-19, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0)


LONG_FORMS = {
    "yo": (2, 1),
    "gu": (2, -1),

    "zo": (3, 1),
    "ru": (3, -1),

    "lo": (4, 1),
    "lu": (4, -1),
    "ilo": (4, 1),
    "ilu": (4, -1),

    "tho": (5, 1),
    "thu": (5, -1),

    "so": (6, 1),
    "su": (6, -1),
    "iso": (6, 1),
    "isu": (6, -1),

    "no": (7, 1),
    "nu": (7, -1),
    "ino": (7, 1),
    "inu": (7, -1),

    "twetho": (8, 1),
    "twethu": (8, -1),

    "tweno": (9, 1),
    "twenu": (9, -1),

    "thiwo": (10, 1),
    "thiwu": (10, -1),
}


ABBREVIATIONS = {
    "y": (2, 1),
    "g": (2, -1),

    "z": (3, 1),
    "r": (3, -1),

    "1o": (4, 1),
    "1u": (4, -1),

    "3o": (5, 1),
    "3u": (5, -1),

    "17o": (6, 1),
    "17u": (6, -1),

    "19o": (7, 1),
    "19u": (7, -1),

    "23o": (8, 1),
    "23u": (8, -1),

    "29o": (9, 1),
    "29u": (9, -1),

    "31o": (10, 1),
    "31u": (10, -1),
}
COLOR_PREFIXES = tuple(ABBREVIATIONS.keys())


UNICODE_EXPONENTS = {
    "⁰": 0,
    "¹": 1,
    "²": 2,
    "³": 3,
    "⁴": 4,
    "⁵": 5,
    "⁶": 6,
    "⁷": 7,
    "⁸": 8,
    "⁹": 9,
}


# TODO: Exponents larger than 9
def parse_exponent(token):
    num = 1
    if token[0] == "^":
        token = token[1:]
        num = int(token[0])
        token = token[1:]
    elif token[0] in UNICODE_EXPONENTS:
        num = 0
        while token[0] in UNICODE_EXPONENTS:
            num *= 10
            num += UNICODE_EXPONENTS[token[0]]
            token = token[1:]
    return token, num


class ColorParsingError(Exception):
    pass


def monzo_from_parts(stepspan, magnitude, off_white_monzo):
    span_prime = dot(off_white_monzo, PSEUDO_EDO_MAPPING)
    magnitude_prime = round((2 * (stepspan - span_prime) + off_white_monzo.sum()) / 7)
    a = -3*(stepspan - span_prime) - 11 * (magnitude - magnitude_prime)
    b = 2*(stepspan - span_prime) + 7 * (magnitude - magnitude_prime)

    result = off_white_monzo + 0
    result[0] = a
    result[1] = b
    return result


def parse_interval(token):
    monzo = zeros(len(PSEUDO_EDO_MAPPING))
    magnitude = 0
    while token[0] == "L":
        token = token[1:]
        token, exponent = parse_exponent(token)
        magnitude += exponent
    while token[0] == "s":
        token = token[1:]
        token, exponent = parse_exponent(token)
        magnitude -= exponent
    while True:
        for prefix in COLOR_PREFIXES:
            if token.startswith(prefix):
                token = token[len(prefix):]
                index, amount = ABBREVIATIONS[prefix]
                token, exponent = parse_exponent(token)
                monzo[index] += amount * exponent
                break
        else:
            break
    if token[0] == "w":
        token = token[1:]
    wa_commas = 0
    while token[0] == "p":
        wa_commas += 1
        token = token[1:]
    while token[0] == "q":
        wa_commas -= 1
        token = token[1:]
    stepspan = int(token)
    stepspan -= sign(stepspan)
    return monzo_from_parts(stepspan, magnitude, monzo) + wa_commas * array(WA_COMMA)
