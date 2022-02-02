# coding: utf-8
from collections import defaultdict
from roman import fromRoman, InvalidRomanNumeralError
from numpy import dot, zeros, sign, array
from .util import Splitter
from .pythagoras import parse_pitch, BASIC_PITCHES
from .monzo import PRIMES, fraction_to_monzo


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

REVERSE_ABBREVIATIONS = defaultdict(list)
for key, (index, _sign) in ABBREVIATIONS.items():
    if _sign < 0:
        REVERSE_ABBREVIATIONS[index].append(key)
    else:
        REVERSE_ABBREVIATIONS[index].insert(0, key)

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

REVERSE_UNICODE_EXPONENTS = {"-": "⁻"}
for key, value in UNICODE_EXPONENTS.items():
    REVERSE_UNICODE_EXPONENTS[str(value)] = key


def int_to_unicode_exponent(n):
    result = ""
    for char in str(n):
        result += REVERSE_UNICODE_EXPONENTS[char]
    return result


def fraction_to_color(token):
    monzo, unrepresentable = fraction_to_monzo(token)
    if unrepresentable != 1:
        raise ColorParsingError("Too high primes for color conversion")
    result = ""
    for index in range(2, len(PRIMES)):
        value = monzo[index]
        if value > 0:
            prefix = REVERSE_ABBREVIATIONS[index][0]
        if value < 0:
            prefix = REVERSE_ABBREVIATIONS[index][1]
            value = abs(value)
        if value > 1:
            prefix += int_to_unicode_exponent(value)
        if value > 0:
            result = prefix + result
    if not result:
        result = "w"
    stepspan = dot(PSEUDO_EDO_MAPPING, monzo)
    if stepspan >= 0:
        degree = stepspan + 1
    else:
        degree = stepspan - 1
    magnitude = 0
    for value in monzo[1:]:
        magnitude += value
    magnitude = round(magnitude/7)
    prefix = ""
    if magnitude < 0:
        prefix = "s"
    if magnitude > 0:
        prefix = "L"
    if abs(magnitude) > 1:
        prefix += int_to_unicode_exponent(abs(magnitude))
    return prefix + result + str(degree)


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


def decompose(monzo):
    zero = monzo*0
    remaining = monzo + 0
    while remaining.any():
        for i in range(len(monzo)):
            if remaining[i]:
                piece = zero + 0
                piece[i] = sign(remaining[i])
                remaining[i] -= piece[i]
                yield piece


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

    if token[0] in BASIC_PITCHES:
        if monzo[0] or monzo[1] or magnitude:
            raise ColorParsingError("Only pythagorean absolute pitches supported")
        token, base = parse_pitch(token)
        result = monzo * 0
        result[:2] = base
        for piece in decompose(monzo):
            result += monzo_from_parts(0, 0, piece)
        return result, True
    else:
        try:
            stepspan = fromRoman(token)
        except InvalidRomanNumeralError:
            stepspan = int(token)
        stepspan -= sign(stepspan)
        result = monzo_from_parts(stepspan, magnitude, monzo) + wa_commas * array(WA_COMMA)
        return result, False


def has_symbol(token, symbols):
    for symbol in symbols:
        if token.startswith(symbol) and len(token) > len(symbol) and token[len(symbol)].isdigit():
            return True
    return False


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


def make_subharmonic_chord(limit, full=False, close_voicing=False):
    if limit % 2 == 0 and not full:
        raise ColorParsingError("Only full subharmonic chords can be even")

    result = []
    skip = 1 if full else 2
    if close_voicing:
        if limit == 1:
            return ["6/6"]
        if limit == 3:
            return ["6/6", "6/4"]
        if limit == 5:
            return ["6/6", "6/5", "6/4"]
        for i in reversed(range(7, limit+1, skip)):
            result.append("{}/{}".format(limit, i))
        return result + ["{}/6".format(limit), "{}/5".format(limit), "{}/4".format(limit)]
    else:
        for i in reversed(range(1, limit+1, skip)):
            result.append("{}/{}".format(limit, i))
        return result


TONE_SPLITTER = Splitter(("+", "no", "\\"))


def degree_key(token):
    degree_token = ""
    while token[-1] in "1234567890":
        degree_token = token[-1] + degree_token
        token = token[:-1]
    return int(degree_token)


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

    chord = None

    if token.lstrip("Ls").startswith(COLOR_PREFIXES):
        if token[-1].isdigit():
            num = ""
            while token[-1].isdigit():
                num = token[-1] + num
                token = token[:-1]
            num = int(num)
        else:
            num = 5
        prefix = token
        chord = []
        for i in range(1, num+1, 2):
            if i % 4 == 1:
                chord.append("w{}".format(i))
            else:
                chord.append("{}{}".format(prefix, i))
        if num == 6:
            chord.append("{}6".format(prefix))

    elif has_symbol(token, ["h", "hw", "hf", "hwf", "hfw"]):
        token = token[1:]
        full = False
        close_voicing = True
        if token[0] == "f":
            full = True
            token = token[1:]
        if token[0] == "w":
            close_voicing = False
            token = token[1:]
        if token[0] == "f":
            full = True
            token = token[1:]
        chord = make_harmonic_chord(int(token), full, close_voicing)

        for tone in removed_tones[:]:
            if tone > 13:
                for harmonic in ["{}/1".format(tone), "{}/4".format(tone)]:
                    if harmonic in chord:
                        chord.remove(harmonic)
                        break
                else:
                    raise ColorParsingError("Failed to find harmonic {} to remove".format(tone))

        for tone in added_tones[:]:
            if tone.isdigit():
                harmonic = int(tone)
                if harmonic > 13:
                    chord.append("{}{}".format(tone, chord[0][1:]))
                    added_tones.remove(tone)

        chord = [fraction_to_color(tone) for tone in chord]

    elif has_symbol(token, ["s", "sw", "sf", "swf", "sfw"]):
        token = token[1:]
        full = False
        close_voicing = True
        if token[0] == "f":
            full = True
            token = token[1:]
        if token[0] == "w":
            close_voicing = False
            token = token[1:]
        if token[0] == "f":
            full = True
            token = token[1:]
        if token == "6":
            chord = ["w1", "g3", "w5", "r6"]
        else:
            chord = make_subharmonic_chord(int(token), full, close_voicing)
            chord = [fraction_to_color(tone) for tone in chord]

    if chord is None:
        return None

    for tone in removed_tones:
        tone = str(tone)
        for t in chord[:]:
            if t.endswith(tone):
                chord.remove(t)

    for tone in added_tones:
        if tone.isdigit():
            tone = "w" + tone
        chord.append(tone)

    chord.sort(key=degree_key)

    return chord
