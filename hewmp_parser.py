from io import StringIO
from numpy import array, zeros, log, floor
from fractions import Fraction
from lexer import Lexer, CONFIGS
from chord_parser import expand_chord, separate_by_arrows
from temperaments import TEMPERAMENTS
from temperament import temper_subgroup, comma_reduce
from notation import notate_fraction, notate_otonal_utonal


# TODO:
# * Ties using time addition commands [+2]
# * Play control
#   - Playhead (loop region start) |> (playhead only) |!>
#   - Loop region end <|
#   - Stop playing >|
# * Parsing of absolute pitches
# * Production of absolute pitches, intervals, ratios and monzos
# * Inline messages
# * Dynamics
# * Chance operators
# * Vibrato
# * Tremolo
# * Pitch-bends
# * It's probably a good idea to attach most of these things to the notes themselves even if treated as events in Python
# * Arpeggios
#   - Arpeggiate and hold [~]
#   - Arpeggiate and hold in sixteenth notes [~1/16]
#   - Arpeggiate and hold evenly (as a tuplet) [~?]
#   - Arpeggiate up in sixteenth notes [^1/16]
#   - Arpeggiate down evenly [v?] (In reverse listed order. Don't measure pitch. Remember to fix chord spellings for this.)
#   - Arpeggiate up and down in a loop [^v1/16]
# * Swing
# * Dynamic tempo
# * Dynamic tuning

class MusicBase:
    def __init__(self, time, duration):
        self.time = Fraction(time)
        self.duration = Fraction(duration)

    @property
    def end_time(self):
        return self.time + self.duration

    def to_json(self):
        return {
            "time": str(self.time),
            "duration": str(self.duration),
        }

    def retime(self, time, duration):
        pass


class Event(MusicBase):
    def flatten(self):
        return [self]


class Tuning(Event):
    def __init__(self, base_frequency, comma_list, constraints, subgroup, suggested_mapping, time=0, duration=0):
        super().__init__(time, duration)
        self.base_frequency = base_frequency
        self.comma_list = comma_list
        self.constraints = constraints
        self.subgroup = subgroup
        self.suggested_mapping = suggested_mapping

    def to_json(self):
        result = super().to_json()
        result.update({
            "type": "tuning",
            "baseFrequency": self.base_frequency,
            "commaList": [list(comma) for comma in self.comma_list],
            "constraints": [list(constraint) for constraint in self.constraints],
            "subgroup": [list(basis_vector) for basis_vector in self.subgroup],
            "suggestedMapping": list(self.suggested_mapping),
        })
        return result

    def retime(self, time, duration):
        # TODO: Deep copy
        return self.__class__(self.base_frequency, self.comma_list, self.constraints, self.subgroup, self.suggested_mapping, time, duration)


class Tempo(Event):
    def __init__(self, beat_duration, unit, swing_amount=0, swing_unit=None, time=0, duration=0):
        super().__init__(time, duration)
        self.beat_duration = beat_duration
        self.unit = unit
        self.swing_amount = swing_amount
        if swing_unit is None:
            self.swing_unit = self.unit
        else:
            self.swing_unit = swing_unit

    def to_json(self):
        result = super().to_json()
        result.update({
            "type": "tempo",
            "beatDuration": str(self.beat_duration),
            "unit": str(self.unit),
            "swingAmount": str(self.swing_amount),
            "swingUnit": str(self.swing_unit),
        })
        return result

    def retime(self, time, duration):
        return self.__class__(self.beat_duration, self.unit, self.swing_amount, self.swing_unit, time, duration)

    def to_realtime(self, time, duration):
        end_beat = float(time + duration)
        start_beat = float(time)
        amount = float(self.swing_amount)
        unit = float(self.swing_unit/self.unit)
        start_time = start_beat + amount*abs(start_beat - floor(0.5*start_beat/unit + 0.5)*2*unit)
        end_time = end_beat + amount*abs(end_beat - floor(0.5*end_beat/unit + 0.5)*2*unit)
        beat_duration = float(self.beat_duration)
        return start_time*beat_duration, (end_time - start_time)*beat_duration


class Rest(Event):
    def __init__(self, emit=False, time=0, duration=1):
        super().__init__(time, duration)
        self.emit = emit

    def flatten(self):
        if self.emit:
            return super().flatten()
        return []

    def to_json(self):
        if self.emit:
            result = super().to_json()
            result["type"] = "rest"
            return result
        return None

    def retime(self, time, duration):
        return self.__class__(self.emit, time, duration)


class Playhead(Event):
    def __init__(self, time=0, duration=0):
        super().__init__(time, duration)

    def retime(self, time, duration):
        return self.__class__(time, duration)


class Playstop(Playhead):
    pass


class Transposable:
    def transpose(self, pitch):
        pass


class Note(Event, Transposable):
    def __init__(self, pitch, time=0, duration=1):
        super().__init__(time, duration)
        self.pitch = pitch


    def transpose(self, pitch):
        self.pitch = self.pitch + pitch

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.pitch, self.time, self.duration)

    def to_json(self):
        result = super().to_json()
        result.update({
            "type": "note",
            "pitch": list(self.pitch),
        })
        return result

    def retime(self, time, duration):
        return self.__class__(array(self.pitch), time, duration)


class Pattern(MusicBase, Transposable):
    def __init__(self, subpatterns=None, time=0, duration=1):
        super().__init__(time, duration)
        if subpatterns is None:
            self.subpatterns = []
        else:
            self.subpatterns = subpatterns

    def __bool__(self):
        return bool(self.subpatterns)

    def insert(self, index, value):
        self.subpatterns.insert(index, value)

    def append(self, subpattern):
        self.subpatterns.append(subpattern)

    def pop(self, index=-1):
        return self.subpatterns.pop(index)

    def __getitem__(self, index):
        return self.subpatterns[index]

    def __len__(self):
        return len(self.subpatterns)

    def __iter__(self):
        return iter(self.subpatterns)

    @property
    def logical_duration(self):
        result = 0
        for subpattern in self.subpatterns:
            result = max(result, subpattern.end_time)
        return result

    def flatten(self):
        logical_duration = self.logical_duration
        if logical_duration == 0:
            dilation = Fraction(0)
        else:
            dilation = self.duration/self.logical_duration
        result = []
        for subpattern in self.subpatterns:
            for event in subpattern.flatten():
                result.append(event.retime(
                    self.time + event.time*dilation,
                    event.duration*dilation
                ))
        return result

    def transpose(self, pitch):
        for subpattern in self.subpatterns:
            if isinstance(subpattern, Transposable):
                subpattern.transpose(pitch)

    def to_json(self):
        start_time = None
        end_time = None
        flat = []
        tempo = None
        for event in self.flatten():
            if isinstance(event, Playhead):
                start_time = event.time
            elif isinstance(event, Playstop):
                end_time = event.end_time
            else:
                flat.append(event)
            if isinstance(event, Tempo):
                tempo = event
        events = []
        # TODO: Integrate tempo changes
        # TODO: Apply swing to playheads
        for event in flat:
            if start_time is not None and event.time < start_time:
                continue
            if end_time is not None and event.end_time > end_time:
                continue
            if start_time is not None:
                event = event.retime(event.time - start_time, event.duration)
            data = event.to_json()
            realtime, realduration = tempo.to_realtime(event.time, event.duration)
            data["realtime"] = realtime
            data["realduration"] = realduration
            events.append(data)
        return events

    def retime(self, time, duration):
        raise NotImplementedError("Pattern retiming not implemented")

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.subpatterns, self.time, self.duration)

    def is_chord(self):
        for note in self:
            if not isinstance(note, Note):
                return False
            if note.time != 0 or note.duration != 1:
                return False
        return True


PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31)
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
    # This particular inflection for 13 was chosen so that the barbados tetrad 10:13:15 is spelled P1:M3+i:P5 or just =Mi+ using the chord system
    "i": [9, -8, 0, 0, 0, 1],
    "!": [-9, 8, 0, 0, 0, -1],
    "*": [-12, 5, 0, 0, 0, 0, 1],
    "%": [12, -5, 0, 0, 0, 0, -1],
    "A": [-9, 3, 0, 0, 0, 0, 0, 1],
    "V": [9, -3, 0, 0, 0, 0, 0, -1],
    "u": [5, -6, 0, 0, 0, 0, 0, 0, 1],
    "d": [-5, 6, 0, 0, 0, 0, 0, 0, -1],
    "U": [-8, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    "D": [8, -2, 0, 0, 0, 0, 0, 0, 0, -1],
    "M": [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1],
    "W": [-5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
}
ARROWS = ""

for key, value in list(DEFAULT_INFLECTIONS.items()):
    ARROWS += key
    DEFAULT_INFLECTIONS[key] = array(value + [0] * (PITCH_LENGTH - len(value)))


DEFAULT_CONFIG = {
    "a": 440,
    "T": None,
    "CL": [],
    "SG": list(map(str, PRIMES)),
    "C": [],
    "CRD": 5,
    "WF": None,
    "L": Fraction(1, 4),
    "beat_duration": Fraction(1),
    "G": 1.0,
    "F": []
}


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


# The following are reserved by something more important:
# A - augmented
# b - flat
# c - cents
# d - diminished
# f - forte
ABSOLUTE_PITCH_LETTERS = "aBCDEFG"


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


def parse_otonal(token, trasposition, *conf):
    subtokens = token.split(":")
    pitches = []
    for subtoken in subtokens:
        pitch, absolute = parse_interval(subtoken, *conf)
        if absolute:
            raise ParsingError("Otonal chord using absolute pitches")
        pitches.append(pitch)
    for i in range(len(pitches)):
        pitches[i] -= pitches[0]
    return Pattern([Note(pitch + trasposition) for pitches in pitches])


def parse_utonal(token, trasposition, *conf):
    subtokens = token.split(";")
    pitches = []
    for subtoken in subtokens:
        pitch, absolute = parse_interval(subtoken, *conf)
        if absolute:
            raise ParsingError("Utonal chord using absolute pitches")
        pitches.append(pitch)
    root = pitches[0]
    for i in range(len(pitches)):
        pitches[i] = root - pitches[i]
    return Pattern([Note(pitch + trasposition) for pitches in pitches])


def parse_chord(token, trasposition, *conf):
    inversion = 0
    if "_" in token:
        token, inversion_token = token.split("_")
        inversion = int(inversion_token)
    if ":" in token:
        result = parse_otonal(token, trasposition, *conf)
    elif ";" in token:
        result = parse_utonal(token, trasposition, *conf)
    else:
        subtokens = expand_chord(token)
        result = Pattern()
        for subtoken in subtokens:
            pitch, absolute = parse_interval(subtoken, *conf)
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


def comma_reduce_pattern(pattern, comma_list, persistence):
    if isinstance(pattern, Note):
        pattern.pitch = comma_reduce(pattern.pitch, comma_list, persistence)
    if isinstance(pattern, Pattern):
        for subpattern in pattern:
            comma_reduce_pattern(subpattern, comma_list, persistence)


class RepeatExpander:
    def __init__(self, lexer):
        self.lexer = lexer

    def __iter__(self):
        self.repeated_section = []
        self.record_mode = False
        self.playback_mode = False
        return self

    def __next__(self):
        while True:
            if self.playback_mode and self.repeated_section:
                return self.repeated_section.pop(0)
            else:
                token = next(self.lexer)

            if token.value == "|:":
                if self.record_mode:
                    raise ParsingError('Nested "|:"')
                self.record_mode = True
                self.playback_mode = False
            elif token.value == ":|":
                if not self.record_mode:
                    raise ParsingError('Unmatched ":|"')
                num_repeats_token = self.lexer.peek()
                if not num_repeats_token.is_end() and num_repeats_token.value.startswith("x"):
                    num_repeats = int(num_repeats_token.value[1:])
                    self.repeated_section *= num_repeats
                    next(self.lexer)
                else:
                    self.repeated_section *= 2
                self.record_mode = False
                self.playback_mode = True
            else:
                if self.record_mode:
                    if token.is_end():
                        raise ParsingError('Missing ":|"')
                    self.repeated_section.append(token)
                else:
                    return token


def consume_lexer(lexer):
    config_mode = False
    config_key = None
    time_mode = False
    repeat_mode = False
    pattern = Pattern()
    time = Fraction(0)
    stack = []
    transposed_pattern = None
    current_pitch = zero_pitch()
    timestamp = None
    playhead = None
    playstop = None

    config = {}
    config.update(DEFAULT_CONFIG)
    tempo_spec = (Fraction(1, 4), 120)
    swing_spec = (None, Fraction(0))

    for token_obj in lexer:
        if token_obj.is_end():
            break
        token = token_obj.value

        if token in CONFIGS:
            config_key = token[:-1]
            config_mode = True
            continue

        # TODO: Tuning and tempo as timed events
        if config_mode:
            if config_key == "a":
                config[config_key] = float(token)
            if config_key == "T":
                comma_list, subgroup = TEMPERAMENTS[token.strip()]
                config["CL"] = comma_list
                config["SG"] = subgroup.split(".")
            if config_key == "CL":
                config[config_key] = [comma.strip() for comma in token.split(",")]
            if config_key == "SG":
                config[config_key] = [basis_fraction.strip() for basis_fraction in token.split(".")]
            if config_key == "C":
                config[config_key] = [constraint.strip() for constraint in token.split(",")]
            if config_key == "CRD":
                config[config_key] = int(token)
            if config_key == "WF":
                config[config_key] = token.strip()
            if config_key == "L":
                config[config_key] = Fraction(token)
            if config_key == "Q":
                unit, bpm = token.split("=")
                tempo_spec = (Fraction(unit), Fraction(bpm))
            if config_key == "SP":
                if "=" in token:
                    unit, amount = token.split("=")
                    unit = Fraction(unit)
                else:
                    unit = None
                    amount = token
                swing_spec = (unit, Fraction(amount.strip().strip("%"))/100)
            if config_key == "G":
                config[config_key] = float(token)
            if config_key == "F":
                config[config_key] = [flag.strip() for flag in token.split(",")]
            config_mode = False
            continue

        if time_mode:
            if token == "]":
                time_mode = False
            else:
                duration_token = token
                time_token = ""
                if "@" in token:
                    duration_token, time_token = token.split("@", 1)
                if duration_token:
                    if duration_token.startswith("-") or duration_token.startswith("+"):
                        pattern[-1].duration += Fraction(duration_token)
                    else:
                        pattern[-1].duration *= Fraction(duration_token)
                if time_token:
                    if time_token == "T":
                        time = timestamp
                    else:
                        time = Fraction(time_token)
                    pattern[-1].time = time
                    time += pattern[-1].duration
            continue

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
        elif token == "&":
            transposed_pattern = pattern.pop()
        elif token == ",":
            time -= pattern[-1].duration
        elif token.startswith("=") or ":" in token or ";" in token:
            if token_obj.whitespace or not token.startswith("="):
                if pattern:
                    time += pattern[-1].duration
                subpattern_time = time
                subpattern_duration = Fraction(1)
            else:
                replaced = pattern.pop()
                subpattern_time = replaced.time
                subpattern_duration = replaced.duration
            if token.startswith("="):
                token = token[1:]
            subpattern = parse_chord(token, current_pitch, DEFAULT_INFLECTIONS, 12, 2)
            subpattern.time = subpattern_time
            subpattern.duration = subpattern_duration
            pattern.append(subpattern)
        elif token in ("z", "Z"):
            if pattern:
                time += pattern[-1].duration
            rest = Rest((token=="Z"), time)
            pattern.append(rest)
        elif token == "T":
            if pattern:
                timestamp = time + pattern[-1].duration
            else:
                timestamp = time
        elif token == "|>":
            playhead = Playhead(time)
            pattern.append(playhead)
        elif token == ">|":
            playstop = Playstop(time)
            pattern.append(playstop)
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
                if absolute:
                    current_pitch = zero_pitch()
                pitch = current_pitch + interval
                if not floaty:
                    current_pitch = pitch
                if pattern:
                    time += pattern[-1].duration
                note = Note(pitch, time)
                pattern.append(note)

    unit, bpm = tempo_spec
    swing_unit, swing_amount = swing_spec
    beat_duration = Fraction(60) / bpm / unit * config["L"]
    tempo = Tempo(beat_duration, config["L"], swing_amount, swing_unit)
    pattern.insert(0, tempo)

    subgroup = [parse_interval(basis_vector, DEFAULT_INFLECTIONS, 12, 2)[0] for basis_vector in config["SG"]]
    comma_list = [parse_interval(comma, DEFAULT_INFLECTIONS, 12, 2)[0] for comma in config["CL"]]
    constraints = [parse_interval(constraint, DEFAULT_INFLECTIONS, 12, 2)[0] for constraint in config["C"]]
    JI = log(array(PRIMES))
    mapping = temper_subgroup(
        JI,
        [comma[:len(JI)] for comma in comma_list],
        [constraint[:len(JI)] for constraint in constraints],
        [basis_vector[:len(JI)] for basis_vector in subgroup],
    )
    suggested_mapping = zero_pitch()
    suggested_mapping[:len(JI)] = mapping
    suggested_mapping[E_INDEX] = 1
    tuning = Tuning(config["a"], comma_list, constraints, subgroup, suggested_mapping)
    pattern.insert(0, tuning)

    pattern.duration = pattern.logical_duration

    if "CR" in config["F"]:
        comma_reduce_pattern(pattern, comma_list, config["CRD"])

    return pattern


def parse_text(text):
    return consume_lexer(RepeatExpander(Lexer(StringIO(text))))


def parse_file(file):
    if not file.seekable():
        file = StringIO(file.read())
    return consume_lexer(RepeatExpander(Lexer(file)))


def simplify_events(events):
    used = array([False] * len(SEMANTIC))

    for event in events:
        if event["type"] == "note":
            for i, coord in enumerate(event["pitch"]):
                if coord != 0:
                    used[i] = True

    semantic = list(array(SEMANTIC)[used])

    def simplify(pitch):
        result = []
        for coord in array(pitch)[used]:
            if coord == int(coord):
                coord = int(coord)
            result.append(coord)
        return result

    for event in events:
        if event["type"] == "note":
            event["pitch"] = simplify(event["pitch"])

        # TODO: Drop zero subgroup vectors
        if event["type"] == "tuning":
            for key in ["commaList", "constraints", "subgroup"]:
                event[key] = [simplify(vector) for vector in event[key]]
            event["suggestedMapping"] = simplify(event["suggestedMapping"])

    return semantic, events


def notate_pattern_as_fractions(pattern, main=False, absolute_time=False):
    if pattern.duration == 0:
        return ""
    suffix = ""
    if not main:
        if pattern.duration != 1:
            if absolute_time:
                suffix = "[{}@{}]".format(pattern.duration, pattern.time)
            else:
                suffix = "[{}]".format(pattern.duration)
        elif absolute_time:
            suffix = "[@{}]".format(pattern.time)
    if isinstance(pattern, Pattern):
        if pattern.is_chord():
            pitches = []
            for note in pattern:
                pitches.append(note.pitch)
            root_fraction = notate_fraction(pattern[0].pitch, PRIMES, E_INDEX, HZ_INDEX, RAD_INDEX)
            chord = notate_otonal_utonal(pitches, PRIMES)
            return "@{}={}{}".format(root_fraction, chord, suffix)
        subnotations = []
        local_time = Fraction(0)
        for subpattern in pattern:
            if subpattern.duration == 0:
                continue
            local_absolute_time = False
            if subpattern.time != local_time:
                local_absolute_time = True
                local_time = subpattern.time
            subnotations.append(notate_pattern_as_fractions(subpattern, absolute_time=local_absolute_time))
            local_time += subpattern.duration
        if main:
            return " ".join(filter(None, subnotations))
        return "(" + " ".join(filter(None, subnotations)) + ")" + suffix
    if isinstance(pattern, Note):
        return "@{}{}".format(notate_fraction(pattern.pitch, PRIMES, E_INDEX, HZ_INDEX, RAD_INDEX), suffix)
    if isinstance(pattern, Rest):
        if pattern.emit:
            return "Z{}".format(suffix)
        return "z{}".format(suffix)

    return ""


if __name__ == "__main__":
    import argparse
    import sys
    import json

    parser = argparse.ArgumentParser(description='Parse input file (or stdin) in HEWMP notation and output JSON to file (or stdout)')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('--simplify', action='store_true')
    parser.add_argument('--fractional', action='store_true')
    args = parser.parse_args()

    pattern = parse_file(args.infile)
    if args.infile is not sys.stdin:
        args.infile.close()

    if args.fractional:
        args.outfile.write(notate_pattern_as_fractions(pattern, True))
    else:
        semantic = SEMANTIC
        events = pattern.to_json()
        if args.simplify:
            semantic, events = simplify_events(events)
        data = {
            "semantic": semantic,
            "events": events
        }
        json.dump(data, args.outfile)

    if args.outfile is not sys.stdout:
        args.outfile.close()
    else:
        args.outfile.write("\n")
