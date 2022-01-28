# coding: utf-8
from numpy import dot, zeros, sign, array
from .util import Splitter


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
                if prefix[-1] in "ou":
                    while token[0] == prefix[-1]:
                        token = token[1:]
                        amount += ABBREVIATIONS[prefix][1]
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


def make_harmonic_chord(limit, full=False, close_voicing=False):
    if limit % 2 == 0 and not full:
        raise ColorParsingError("Only full harmonic chords can be even")
    result = []
    skip = 1 if full else 2
    if close_voicing:
        if limit == 1:
            return ["4/4"]
        if limit == 3:
            return ["4/4", "6/4"]
        if limit == 5:
            return ["4/4", "5/4", "6/4"]
        for i in range(7, limit+1, skip):
            result.append("{}/4".format(i))
        return ["4/4", "5/4", "6/4"] + result
    else:
        for i in range(1, limit+1, skip):
            result.append("{}/1".format(i))
        return result


TONE_SPLITTER = Splitter(("+", "no", "\\"))


def expand_chord(token):
    token, tones = TONE_SPLITTER(token)
    added_tones = tones["+"]
    removed_tones = tones["no"]
    replacements = tones["\\"]

    for replacement in replacements:
        added_tones.append(replacement)
        if replacement[-1] in "24":
            removed_tones.append(3)
        else:
            removed_tones.append(replacement[-1])

    removed_tones = [int(tone) for tone in removed_tones]

    if token[0] == "h":
        token = token[1:]
        full = False
        close_voicing = False
        if token[0] == "f":
            full = True
            token = token[1:]
        if token[0] == "c":
            close_voicing = True
            token = token[1:]
        if token[0] == "f":
            full = True
            token = token[1:]
        chord = make_harmonic_chord(int(token), full, close_voicing)

        for tone in removed_tones:
            if tone == 5:
                if "3/1" in chord:
                    chord.remove("3/1")
                if "6/4" in chord:
                    chord.remove("6/4")
            if tone == 3:
                if "5/1" in chord:
                    chord.remove("5/1")
                if "5/4" in chord:
                    chord.remove("5/4")
            for harmonic in ["{}/1".format(tone), "{}/4".format(tone)]:
                if harmonic in chord:
                    chord.remove(harmonic)
        for tone in added_tones:
            if tone.isdigit():
                tone = int(tone)
                if tone > 13:
                    chord.append("{}{}".format(tone, chord[0][1:]))
                else:
                    chord.append("w{}".format(tone))
            else:
                chord.append(tone)

        # TODO: Convert to colors and sort

        return chord

    # Singal to fall through to other chord parsers
    return None
