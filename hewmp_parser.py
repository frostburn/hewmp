from io import StringIO
from numpy import array, zeros, log
from fractions import Fraction
from lexer import Lexer
from chord_parser import expand_chord, separate_by_arrows


class MusicBase:
    def __init__(self, time, duration):
        self.time = Fraction(time)
        self.duration = Fraction(duration)

    @property
    def end_time(self):
        return self.time + self.duration


class Note(MusicBase):
    def __init__(self, pitch, time=0, duration=1):
        super().__init__(time, duration)
        self.pitch = pitch

    def is_rest(self):
        return self.pitch is None

    def flatten(self):
        return [self]

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.pitch, self.time, self.duration)


class Pattern(MusicBase):
    def __init__(self, subpatterns=None, time=0, duration=1):
        super().__init__(time, duration)
        if subpatterns is None:
            self.subpatterns = []
        else:
            self.subpatterns = subpatterns

    def __bool__(self):
        return bool(self.subpatterns)

    def append(self, subpattern):
        self.subpatterns.append(subpattern)

    def pop(self, index=-1):
        return self.subpatterns.pop(index)

    def __getitem__(self, index):
        return self.subpatterns[index]

    def __len__(self):
        return len(self.subpatterns)

    @property
    def logical_duration(self):
        result = 0
        for subpattern in self.subpatterns:
            result = max(result, subpattern.end_time)
        return result

    def flatten(self):
        dilation = self.duration/self.logical_duration
        result = []
        for subpattern in self.subpatterns:
            for note in subpattern.flatten():
                result.append(Note(
                    note.pitch,
                    self.time + note.time*dilation,
                    note.duration*dilation
                ))
        return result


    def to_json(self):
        events = []
        for note in self.flatten():
            events.append({
                "type": "note",
                "pitch": list(note.pitch),
                "time": str(note.time),
                "duration": str(note.duration),
            })
        return events

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.subpatterns, self.time, self.duration)


PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
E_INDEX = len(PRIMES)
HZ_INDEX = E_INDEX + 1
RAD_INDEX = HZ_INDEX + 1
PITCH_LENGTH = RAD_INDEX + 1

SEMANTIC = []
for prime in PRIMES:
    SEMANTIC.append(str(prime))
SEMANTIC.append("e")
SEMANTIC.append("Hz")
SEMANTIC.append("rad")
SEMANTIC = tuple(SEMANTIC)

DEFAULT_INFLECTIONS = {
    "+": [-4, 4, -1],
    "-": [4, -4, 1],
    ">": [6, -2, 0, -1],
    "<": [-6, 2, 0, 1],
    "^": [-5, 1, 0, 0, 1],
    "v": [5, -1, 0, 0, -1],
    "*": [-1, 3, 0, 0, 0, -1],
    "%": [1, -3, 0, 0, 0, 1],
    "u": [-12, 5, 0, 0, 0, 0, 1],
    "d": [12, -5, 0, 0, 0, 0, -1],
    "U": [-9, 3, 0, 0, 0, 0, 0, 1],
    "D": [9, -3, 0, 0, 0, 0, 0, -1],
    "A": [5, -6, 0, 0, 0, 0, 0, 0, 1],
    "V": [-5, 6, 0, 0, 0, 0, 0, 0, -1],
    "M": [-8, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    "W": [8, -2, 0, 0, 0, 0, 0, 0, 0, -1],
    "i": [5, -4, -1, 0, 0, 1],
    "!": [-5, 4, 1, 0, 0, -1],
}
ARROWS = ""

for key, value in list(DEFAULT_INFLECTIONS.items()):
    ARROWS += key
    DEFAULT_INFLECTIONS[key] = array(value + [0] * (PITCH_LENGTH - len(value)))


def zero_pitch():
    return zeros(PITCH_LENGTH)


class ParsingError(Exception):
    pass


def number_to_pitch(number):
    if number < 1:
        raise ValueError("Non-vectorizable number {}".format(number))
    pitch = zero_pitch()
    for i, p in enumerate(PRIMES):
        while number % p == 0:
            number //= p
            pitch[i] += 1
    pitch[E_INDEX] = log(number)
    return pitch


def parse_fraction(token):
    if "/" in token:
        numerator, denominator = token.split("/", 1)
        numerator = int(numerator)
        denominator = int(denominator)
        return number_to_pitch(numerator) - number_to_pitch(denominator)
    return number_to_pitch(int(token))

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
    "A4": (-9, 6),
    "A1": (-11, 7),
    "A5": (-12, 8),
    "A2": (-14, 9),
    "A6": (-15, 10),
    "A3": (-17, 11),
    "A7": (-18, 12),
}

AUGMENTED_INFLECTION = (-11, 7)
INTERVAL_QUALITIES = "dmPMA"


def parse_arrows(token, inflections):
    quality = token[0]
    token = token[1:]
    augmented = 0
    while token[0] == "A":
        augmented += 1
        token = token[1:]
    while token[0] == "d":
        augmented -= 1
        token = token[1:]

    result = zero_pitch()
    result[0] += AUGMENTED_INFLECTION[0] * augmented
    result[1] += AUGMENTED_INFLECTION[1] * augmented

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
    basic_pitch = BASIC_INTERVALS[lookup]

    result[0] += octave + basic_pitch[0]
    result[1] += basic_pitch[1]

    return result


# Intentionally skips 'b', 'd' and 'A', so as not to confuse them with flat, diminished or augmented
ABSOLUTE_PITCH_LETTERS = "acefgBCDEFG"


# TODO:
def parse_pitch(token):
    pass


def parse_interval(token, inflections, edn_divisions, edn_divided):
    absolute = False
    if token.startswith("@"):
        absolute = True
        token = token[1:]

    direction = None
    if token[0] in "+-":
        if token[0] == "-":
            direction = -1
        else:
            direction = 1
        token = token[1:]

    pitch = zero_pitch()

    if token[0].isdigit():
        if token.endswith("c"):
            cents_in_nats = float(token[:-1])/1200*log(2)
            pitch[E_INDEX] = cents_in_nats
        elif token.endswith("Hz"):
            hz = float(token[:-2])
            pitch[HZ_INDEX] = hz
        elif token.endswith("deg"):
            rad = float(token[:-3]) / 180 * pi
            pitch[RAD_INDEX] = rad
        elif "\\" in token:
            divisions = edn_divisions
            divided = edn_divided
            step_spec = token.split("\\")
            steps = int(step_spec[0])
            if len(step_spec) >= 2:
                divisions = int(step_spec[1])
            if len(step_spec) == 3:
                divided = int(step_spec[2])
            pitch[E_INDEX] = steps / divisions * log(divided)
        else:
            pitch = parse_fraction(token)
    elif token[0] in INTERVAL_QUALITIES:
        pitch = parse_arrows(token, inflections)
    elif token[0] in ABSOLUTE_PITCH_LETTERS:
        if direction is not None:
            raise ParsingError("Signed absolute pitch")
        pitch = parse_pitch(token, inflections)
        absolute = True

    if direction is not None:
        pitch *= direction

    return pitch, absolute


def parse_chord(token, trasposition, *conf):
    inversion = 0
    if "_" in token:
        token, inversion_token = token.split("_")
        inversion = int(inversion_token)
    tokens = expand_chord(token)
    result = Pattern()
    for token in tokens:
        pitch, absolute = parse_interval(token, *conf)
        if absolute:
            result.append(Note(pitch))
        else:
            result.append(Note(pitch + trasposition))
    for i in range(inversion):
        result[i].pitch[0] += 1
    if inversion:
        for i in range(len(result)):  #pylint: disable=consider-using-enumerate
            result[i].pitch[0] -= 1
    return result


# TODO
def parse_otonal():
    pass


# TODO
def parse_utonal():
    pass


def consume_lexer(lexer):
    time_mode = False
    pattern = Pattern()
    time = Fraction(0)
    stack = []
    transposed_pattern = None
    current_pitch = zero_pitch()

    for token_obj in lexer:
        if token_obj.is_end():
            break
        token = token_obj.value

        if time_mode:
            if token == "]":
                time_mode = False
            else:
                pattern[-1].duration *= Fraction(token)
        else:
            if token == "(":
                if pattern:
                    time += pattern[-1].duration
                stack.append((pattern, time))
                pattern = Pattern([], time)
                time = Fraction(0)
            elif token == ")":
                subpattern = pattern
                pattern, time = stack.pop()
                pattern.append(subpattern)
            elif token == "[":
                time_mode = True
            elif token == "]":
                raise ParsingError('Unmatched "]"')
            elif token == "|:":  # TODO
                pass
            elif token == ":|":
                pass
            elif token == "&":
                transposed_pattern = pattern.pop()
            elif token == ",":
                time -= pattern[-1].duration
            elif token.startswith("="):
                if token_obj.whitespace:
                    if pattern:
                        time += pattern[-1].duration
                    subpattern_time = time
                    subpattern_duration = Fraction(1)
                else:
                    replaced = pattern.pop()
                    subpattern_time = replaced.time
                    subpattern_duration = replaced.duration
                subpattern = parse_chord(token[1:], current_pitch, DEFAULT_INFLECTIONS, 12, 2)
                subpattern.time = subpattern_time
                subpattern.duration = subpattern_duration
                pattern.append(subpattern)
            elif ":" in token:
                pattern.append(parse_otonal(token, current_pitch, DEFAULT_INFLECTIONS, 12, 2))
            elif ";" in token:
                pattern.append(parse_utonal(token, current_pitch, DEFAULT_INFLECTIONS, 12, 2))
            else:
                floaty = False
                if token.startswith("~"):
                    floaty = True
                    token = token[1:]
                interval, absolute = parse_interval(token, DEFAULT_INFLECTIONS, 12, 2)

                if transposed_pattern:
                    if absolute:
                        raise ParsingError("Absolute transposition")
                    transposed_pattern.transpose(interval)
                    pattern.append(transposed_pattern)
                    transposed_pattern = None
                else:
                    pitch = current_pitch + interval
                    if not floaty:
                        current_pitch = pitch
                    if pattern:
                        time += pattern[-1].duration
                    note = Note(pitch, time)
                    pattern.append(note)

    pattern.duration = pattern.logical_duration
    return pattern


def parse_text(text):
    return consume_lexer(Lexer(StringIO(text)))


if __name__ == "__main__":
    if False:
        triplet = Pattern([
            Note(array([0, 0]), 0, 1),
            Note(array([-3, 2]), 1, 1),
            Note(array([-1, 1]), 2, 1),
        ], 0, 1)

        print(triplet.flatten())

        nested_tuplet = Pattern([
            triplet,
            Note(array([1, 0]), 1, 1)
        ], 0, 1)

        print(nested_tuplet.flatten())

        nested_tuplet.subpatterns[0].time = Fraction(1)
        nested_tuplet.subpatterns[1].time = Fraction(0)

        print(nested_tuplet.flatten())

    # print(parse_text("3/2 (~1,~5/4,~3/2)[2] (5/4 3/2)[1/2] 1"))
    # print(parse_text("P1 ~M3- ~P5 ~m7<"))

    # print(repr(ARROWS))

    giant_steps = """-P8[0]
|:   P4=M- m3+=dom- | -P5=M-   m3+=dom-_2 | P4=M-_1[2] | A4-=m7+_1 -P5=7-_2 |
    -P5=M- m3+=dom- | -P5=M-   m3+=dom-_2 | P4=M-[2]   | A4-=m7+_1 -P5=7-_2 |
    -P5=M-[2]       | A4-=m7+  -P5=dom-   | P4=M-[2]   | A4-=m7+   -P5=7-   |
    -P5=M-[2]       | A4-=m7+  -P5=dom-   | P4=M-[2]   | m7+=m7+   -P5=7-  :||"""

    melody = """P8[0]
|:  P1[4] -M3-[4] | -m3+[4] -M3-[3] m3+[9] |  A1-[3] -M2[5] |
    P4[4] -M3-[4] | -m3+[4] -M3-[3] m3+[9] |  A1-[4] -M2[3]
    P4[9]         |  A1-[4]  -M2[3]  P4[9] |  A1-[4] -M2[3]
    P4[5]   P1[4] |  A1-[4]  -M2[3]  P4[9] | -M3-[3]  P1[5] :||"""

    # text = "P1=M- M3-=dom-_2 P5"
    # text = giant_steps
    # print(parse_text(text))

    events = parse_text(melody).to_json()
    result = {"semantic": SEMANTIC, "events": events}
    import json
    print(json.dumps(result))
