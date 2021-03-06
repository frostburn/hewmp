# coding: utf-8
from collections import defaultdict
from roman import fromRoman, InvalidRomanNumeralError
from numpy import dot, zeros, sign, array, log
from .util import Splitter
from .pythagoras import PITCH_LETTERS
from . import pythagoras
from .monzo import PRIMES, fraction_to_monzo


PSEUDO_EDO_MAPPING = (7, 11, 16, 20, 24, 26, 29, 30, 32, 34, 37)


MAX_HARMONIC_CHORD = 36


LONG_FORMS = {
    "a": "",

    "la": "L",
    "sa": "s",

    "wa": "w",

    "yo": "y",
    "gu": "g",

    "zo": "z",
    "ru": "r",

    "lo": "1o",
    "lu": "1u",
    "ilo": "1o",
    "ilu": "1u",

    "tho": "3o",
    "thu": "3u",

    "so": "17o",
    "su": "17u",
    "iso": "17o",
    "isu": "17u",

    "no": "19o",
    "nu": "19u",
    "ino": "19o",
    "inu": "19u",

    "twetho": "23o",
    "twethu": "23u",

    "tweno": "29o",
    "twenu": "29u",

    "thiwo": "31o",
    "thiwu": "31u",
}


LONG_EXPONENTS = {
    "bi": "²",
    "tri": "³",
    "quad": "⁴",
    "quin": "⁵",
    "sep": "⁷",
    "le": "¹¹",
    "the": "¹³",
    "se": "¹⁷",
    "ne": "¹⁹",
    "twethe": "²³",
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

    "¹¹": 11,
    "¹³": 13,
    "¹⁷": 17,
    "¹⁹": 19,
    "²³": 23,
}

REVERSE_UNICODE_EXPONENTS = {"-": "⁻"}
for key, value in UNICODE_EXPONENTS.items():
    REVERSE_UNICODE_EXPONENTS[str(value)] = key


def int_to_unicode_exponent(n):
    result = ""
    for char in str(n):
        result += REVERSE_UNICODE_EXPONENTS[char]
    return result


class Interval:
    absolute = False

    def __init__(self, stepspan, magnitude, off_white_monzo, po_qu=0):
        self.stepspan = stepspan
        self.magnitude = magnitude
        self.off_white_monzo = off_white_monzo
        self.po_qu = po_qu

    @property
    def interval_class(self):
        if self.stepspan >= 0:
            return self.stepspan + 1
        return self.stepspan - 1

    def monzo(self):
        stepspan = self.stepspan - self.po_qu
        span_prime = dot(self.off_white_monzo, PSEUDO_EDO_MAPPING)
        magnitude_prime = round((2 * (stepspan - span_prime) + self.off_white_monzo.sum()) / 7)
        a = -3*(stepspan - span_prime) - 11 * (self.magnitude - magnitude_prime)
        b = 2*(stepspan - span_prime) + 7 * (self.magnitude - magnitude_prime)

        result = self.off_white_monzo + 0
        result[0] = a
        result[1] = b
        return result


class Pitch:
    absolute = True

    def __init__(self, spine, off_white_monzo):
        self.spine = spine
        self.off_white_monzo = off_white_monzo

    def monzo(self):
        result = self.off_white_monzo + self.spine.monzo()
        for piece in decompose(self.off_white_monzo):
            # TODO: Optimize into plain lookups
            span_prime = dot(piece, PSEUDO_EDO_MAPPING)
            magnitude_prime = round((-2*span_prime + piece.sum()) / 7)
            a = 3 * span_prime + 11 * magnitude_prime
            b = -2 * span_prime - 7 * magnitude_prime
            result[0] += a
            result[1] += b
        return result


def monzo_to_color(monzo):
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
    return prefix + result + str(int(degree))


def fraction_to_color(token):
    monzo, unrepresentable = fraction_to_monzo(token)
    if unrepresentable != 1:
        raise ColorParsingError("Too high primes for color conversion")
    return monzo_to_color(monzo)


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
    po_qu = 0
    while token[0] == "p":
        po_qu += 1
        token = token[1:]
    while token[0] == "q":
        po_qu -= 1
        token = token[1:]

    if token[0] in PITCH_LETTERS:
        if monzo[0] or monzo[1] or magnitude:
            raise ColorParsingError("Only pythagorean absolute pitches supported")
        token, spine = pythagoras.Pitch.parse(token)
        return Pitch(spine, monzo)
    else:
        try:
            stepspan = fromRoman(token)
        except InvalidRomanNumeralError:
            stepspan = int(token)
        stepspan -= sign(stepspan)
        return Interval(stepspan, magnitude, monzo, po_qu)


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


CHORD_PREFIXES = COLOR_PREFIXES + ('w',)


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

    if token == "5":
        chord = ["w1", "w5"]

    elif token.lstrip("Ls").startswith(CHORD_PREFIXES):
        if token[-1].isdigit():
            num = ""
            while token[-1].isdigit():
                num = token[-1] + num
                token = token[:-1]
            num = int(num)
            if num == 5:
                chord = ["w1", "{}5".format(token)]
                num = False
        else:
            num = 5
        prefix = token
        if num:
            chord = []
            for i in range(1, num+1, 2):
                if i % 4 == 1:
                    chord.append("w{}".format(i))
                else:
                    chord.append("{}{}".format(prefix, i))
            if num == 6:
                chord.append("{}6".format(prefix))

    elif has_symbol(token, ["h", "ht", "hf", "htf", "hft"]):
        token = token[1:]
        full = False
        close_voicing = True
        if token[0] == "f":
            full = True
            token = token[1:]
        if token[0] == "t":
            close_voicing = False
            token = token[1:]
        if token[0] == "f":
            full = True
            token = token[1:]
        limit = int(token)
        if limit > MAX_HARMONIC_CHORD:
            raise ColorParsingError("Too large harmonic chord")
        chord = make_harmonic_chord(limit, full, close_voicing)

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

    elif has_symbol(token, ["s", "st", "sf", "stf", "sft"]):
        token = token[1:]
        full = False
        close_voicing = True
        if token[0] == "f":
            full = True
            token = token[1:]
        if token[0] == "t":
            close_voicing = False
            token = token[1:]
        if token[0] == "f":
            full = True
            token = token[1:]
        if token == "6":
            chord = ["w1", "g3", "w5", "r6"]
        else:
            limit = int(token)
            if limit > MAX_HARMONIC_CHORD:
                raise ColorParsingError("Too large subharmonic chord")
            chord = make_subharmonic_chord(limit, full, close_voicing)
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


JI = log(PRIMES)


def parse_comma(token):
    token = token.lower().replace("-", "")
    short_token = ""
    modified = True
    fresh = False
    while modified:
        fresh = False
        modified = False
        exponent = None
        exponents = []
        while True:
            for name, exponent_ in LONG_EXPONENTS.items():
                if token.startswith(name):
                    exponents.append(exponent_)
                    token = token[len(name):]
                    break
            else:
                break
        if exponents:
            fresh = True
            m = 1
            for exponent_ in exponents:
                m *= UNICODE_EXPONENTS[exponent_]
            exponent = "".join(REVERSE_UNICODE_EXPONENTS[c] for c in str(m))
        while True:
            done = False
            for long_form, short_form in LONG_FORMS.items():
                if token.startswith(long_form):
                    short_token += short_form
                    token = token[len(long_form):]
                    modified = True
                    if long_form == "a":
                        done = True
                        break
                    if exponent:
                        short_token += exponent
                    if long_form in ("sa", "la"):
                        done = True
                    break
            else:
                break
            if done:
                break
    if exponent is None or not fresh:
        ordinal = 1
    else:
        ordinal = UNICODE_EXPONENTS[exponent]

    token = short_token + token

    segment = []
    degree = -2
    while True:
        monzo = parse_interval("{}{}".format(token, degree)).monzo()
        nats = dot(JI, monzo)
        if nats < 0:
            break
        segment.append((nats, monzo))
        degree -= 1
    degree = 1
    while len(segment) < 7:
        monzo = parse_interval("{}{}".format(token, degree)).monzo()
        nats = dot(JI, monzo)
        if nats > 0:
            segment.append((nats, monzo))
        degree += 1

    segment.sort()
    return segment[ordinal - 1][1]


if __name__ == "__main__":
    import argparse
    from .notation import tokenize_fraction

    parser = argparse.ArgumentParser(description='Parse a color comma into a fraction')
    parser.add_argument('name', type=str)
    args = parser.parse_args()

    monzo = parse_comma(args.name)
    print(tokenize_fraction(monzo, PRIMES))
