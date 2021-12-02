from io import StringIO
from collections import Counter
from numpy import array, zeros, log, floor, pi, around, dot, exp, cumsum, linspace, concatenate
from scipy.interpolate import interp1d
try:
    import mido
except ImportError:
    mido = None
from fractions import Fraction
from lexer import Lexer, CONFIGS, TRACK_START
from chord_parser import expand_chord, separate_by_arrows
from temperaments import TEMPERAMENTS
from temperament import temper_subgroup, comma_reduce
from notation import notate_fraction, notate_otonal_utonal, notate_pitch, reverse_inflections
from percussion import PERCUSSION_SHORTHANDS
from gm_programs import GM_PROGRAMS


# TODO:
# * User-specified gate length
# * User-specified velocity
# * Chance operators
# * Vibrato
# * Tremolo
# * Pitch-bends
# * Arpeggios
#   - Arpeggiate and hold [~]
#   - Arpeggiate and hold in sixteenth notes [~1/16]
#   - Arpeggiate and hold evenly (as a tuplet) [~?]
#   - Arpeggiate up in sixteenth notes [^1/16]
#   - Arpeggiate down evenly [v?] (In reverse listed order. Don't measure pitch. Remember to fix chord spellings for this.)
#   - Arpeggiate up and down in a loop [^v1/16]
# * Dynamic tempo
# * Dynamic tuning
# * Preserve whitespace when translating
# * Translation to relative fractions
# * Integrate comma root solver through a flag
# * Include EDN steps in plain MIDI
# * Playhead control across tracks


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


def zero_pitch():
    return zeros(PITCH_LENGTH)


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
    def __init__(self, base_frequency, comma_list, constraints, subgroup, edn_divisions=None, edn_divided=None, warts=None, suggested_mapping=None, time=0, duration=0):
        super().__init__(time, duration)
        self.base_frequency = base_frequency
        self.comma_list = comma_list
        self.constraints = constraints
        self.subgroup = subgroup
        self.edn_divisions = edn_divisions
        self.edn_divided = edn_divided
        self.warts = warts
        self.suggested_mapping = suggested_mapping

    def suggest_mapping(self):
        JI = log(array(PRIMES))
        if self.edn_divisions is None or self.edn_divided is None or self.warts is None:
            mapping = temper_subgroup(
                JI,
                [comma[:len(JI)] for comma in self.comma_list],
                [constraint[:len(JI)] for constraint in self.constraints],
                [basis_vector[:len(JI)] for basis_vector in self.subgroup],
            )
        else:
            generator = log(float(self.edn_divided)) / float(self.edn_divisions)
            steps = around(JI/generator)
            mapping = steps*generator
            for index, count in enumerate(self.warts):
                modification = ((count + 1)//2) * (2*(count%2) - 1)
                if mapping[index] > JI[index]:
                    steps[index] -= modification
                else:
                    steps[index] += modification
            mapping = steps*generator
        self.suggested_mapping = zero_pitch()
        self.suggested_mapping[:len(JI)] = mapping
        self.suggested_mapping[E_INDEX] = 1

    def to_json(self):
        result = super().to_json()
        comma_list = ",".join(notate_fraction(comma, PRIMES) for comma in self.comma_list)
        constraints = ",".join(notate_fraction(constraint, PRIMES) for constraint in self.constraints)
        subgroup = ".".join(notate_fraction(basis_vector, PRIMES) for basis_vector in self.subgroup)
        result.update({
            "type": "tuning",
            "baseFrequency": self.base_frequency,
            "commaList": comma_list,
            "constraints": constraints,
            "subgroup": subgroup,
            "edn": [None if self.edn_divisions is None else str(self.edn_divisions), None if self.edn_divided is None else str(self.edn_divided)],
            "warts": None if self.warts is None else list(self.warts),
            "suggestedMapping": list(self.suggested_mapping),
        })
        return result

    def retime(self, time, duration):
        comma_list = [array(comma) for comma in self.comma_list]
        constraints = [array(constraint) for constraint in self.constraints]
        subgroup = [array(basis_vector) for basis_vector in self.subgroup]
        warts = None if self.warts is None else list(self.warts)
        return self.__class__(
            self.base_frequency,
            comma_list,
            constraints,
            subgroup,
            self.edn_divisions,
            self.edn_divided,
            warts,
            array(self.suggested_mapping),
            time,
            duration
        )

    def copy(self):
        return self.retime(self.time, self.duration)

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.__class__.__name__,
            self.base_frequency,
            self.comma_list,
            self.constraints,
            self.subgroup,
            self.edn_divisions,
            self.edn_divided,
            self.warts,
            self.suggested_mapping,
            self.time,
            self.duration,
        )


class Tempo(Event):
    def __init__(self, tempo_unit, tempo_duration, beat_unit, groove_pattern=None, groove_span=None, time=0, duration=0):
        super().__init__(time, duration)
        self.tempo_unit = tempo_unit
        self.tempo_duration = tempo_duration
        self.beat_unit = beat_unit
        self.groove_pattern = groove_pattern
        self.groove_span = groove_span
        self.calculate_groove()

    @property
    def beat_duration(self):
        return self.tempo_duration * self.beat_unit / self.tempo_unit

    def calculate_groove(self):
        if self.groove_span is None or self.groove_pattern is None:
            self.groove = lambda x: x
            return
        beat_times = concatenate(([0], cumsum(list(map(float, self.groove_pattern)))))
        beat_times /= beat_times.max()
        beats = linspace(0, 1, len(beat_times))
        self.groove = interp1d(beats, beat_times)

    def to_json(self):
        result = super().to_json()
        result.update({
            "type": "tempo",
            "tempoUnit": str(self.tempo_unit),
            "tempoDuration": str(self.tempo_duration),
            "beatUnit": str(self.beat_unit),
            "beatDuration": str(self.beat_duration),
            "groovePattern": list(map(str, self.groove_pattern)),
            "grooveSpan": str(self.groove_span),
        })
        return result

    def retime(self, time, duration):
        return self.__class__(self.tempo_unit, self.tempo_duration, self.beat_unit, self.groove_pattern, self.groove_span, time, duration)

    def copy(self):
        return self.retime(self.time, self.duration)

    def to_realtime(self, time, duration):
        start_beat = float(time)
        end_beat = float(time + duration)
        unit = float(self.groove_span/self.beat_unit)

        groove_bars, groove_beat = divmod(start_beat, unit)
        start_time = (groove_bars + self.groove(groove_beat/unit)) * unit

        groove_bars, groove_beat = divmod(end_beat, unit)
        end_time = (groove_bars + self.groove(groove_beat/unit)) * unit

        beat_duration = float(self.beat_duration)
        return start_time*beat_duration, (end_time - start_time)*beat_duration

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.__class__.__name__,
            self.tempo_unit,
            self.tempo_duration,
            self.beat_unit,
            self.groove_pattern,
            self.groove_span,
            self.time,
            self.duration,
        )


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


class Dynamic(Event):
    def __init__(self, velocity, time=0, duration=0):
        super().__init__(time, duration)
        self.velocity = velocity

    def retime(self, time, duration):
        return self.__class__(self.velocity, time ,duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "dynamic"
        result["velocity"] = str(self.velocity)
        return result


class Articulation(Event):
    def __init__(self, gate_ratio, time=0, duration=0):
        super().__init__(time, duration)
        self.gate_ratio = gate_ratio

    def retime(self, time, duration):
        return self.__class__(self.gate_ratio, time ,duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "articulation"
        result["gateRatio"] = str(self.gate_ratio)
        return result


class ControlChange(Event):
    def __init__(self, control, value, time=0, duration=0):
        super().__init__(time, duration)
        self.control = control
        self.value = value

    def retime(self, time, duration):
        return self.__class__(self.control, self.value, time, duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "controlChange"
        result["subtype"] = "controlChange"
        result["control"] = self.control
        result["value"] = self.value
        return result


class TrackVolume(ControlChange):
    def __init__(self, volume, time=0, duration=0):
        super().__init__(7, None, time, duration)
        self.volume = volume

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self.value = int(round(127*value))
        self._volume = value

    def retime(self, time, duration):
        return self.__class__(self.volume, time ,duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "trackVolume"
        result["volume"] = str(self.volume)
        return result


class UserMessage(Event):
    def __init__(self, message, time, duration=0):
        super().__init__(time, duration)
        self.message = message

    def retime(self, time, duration):
        return self.__class__(self.message, time, duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "userMessage"
        result["message"] = self.message
        return result


class ProgramChange(Event):
    def __init__(self, name, program, time, duration=0):
        super().__init__(time, duration)
        self.name = name
        self.program = program

    def retime(self, time, duration):
        return self.__class__(self.name, self.program, time, duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "programChange"
        result["name"] = self.name
        result["program"] = self.program
        return result


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


class Percussion(Event):
    def __init__(self, name, index=None, time=0, duration=1):
        super().__init__(time, duration)
        self.name = name
        self.index = index

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r})".format(self.__class__.__name__, self.name, self.index, self.time, self.duration)

    def to_json(self):
        result = super().to_json()
        result.update({
            "type": "percussion",
            "name": self.name,
            "index": self.index,
        })
        return result

    def retime(self, time, duration):
        return self.__class__(self.name, self.index, time, duration)


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
        tuning = None
        for event in self.flatten():
            if isinstance(event, Playhead):
                start_time = event.time
            elif isinstance(event, Playstop):
                end_time = event.end_time
            else:
                flat.append(event)
            if isinstance(event, Tempo):
                tempo = event
            if isinstance(event, Tuning):
                tuning = event
        events = []

        articulation = None
        missing = {
            Articulation: None,
            Dynamic: None,
            ProgramChange: None,
            TrackVolume: None,
        }
        if start_time is not None:
            start_realtime, _ = tempo.to_realtime(start_time, 0)
        else:
            start_realtime = 0.0
        for event in flat:
            if isinstance(event, Articulation):
                articulation = event
            realtime, realduration = tempo.to_realtime(event.time, event.duration)
            if isinstance(event, Note) or isinstance(event, Percussion):
                _, real_gate_length = tempo.to_realtime(event.time, event.duration * articulation.gate_ratio)
            else:
                real_gate_length = None
            if start_time is not None and event.time < start_time:
                for type_ in missing:
                    if isinstance(event, type_):
                        missing[type_] = event
                continue
            if end_time is not None and event.end_time > end_time:
                continue
            if start_time is not None:
                event = event.retime(event.time - start_time, event.duration)
            data = event.to_json()
            data["realtime"] = realtime - start_realtime
            data["realduration"] = realduration
            if real_gate_length is not None:
                data["realGateLength"] = float(real_gate_length)
            for type_, missing_event in list(missing.items()):
                if missing_event is not None:
                    extra = missing_event.retime(event.time, 0)
                    extra_data = extra.to_json()
                    extra_data["realtime"] = data["realtime"]
                    events.append(extra_data)
                    missing[type_] = None
            events.append(data)

        if start_time is None:
            start_time = self.time
        if end_time is None:
            end_time = self.end_time
        if start_time > tempo.time:
            events.insert(0, tempo.to_json())
        if start_time > tuning.time:
            events.insert(0, tuning.to_json())
        duration = end_time - start_time
        realtime, realduration = tempo.to_realtime(start_time, duration)
        result = {
            "time": str(start_time),
            "duration": str(duration),
            "realtime": realtime,
            "realduration": realduration,
            "events": events,
        }
        return result

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


DEFAULT_CONFIG = {
    "tuning": Tuning(440.0, (), (), (), Fraction(12), Fraction(2), None),  # warts is None so it's JI
    "tempo": Tempo(Fraction(1, 4), Fraction(1, 2), Fraction(1, 4)),
    "track_volume": TrackVolume(Fraction(1)),
    "program_change": None,
    "CRD": 5,
    "WF": None,
    "N": "hewmp",
    "flags": ("unmapEDN",),  # default to just intonation
}

DEFAULT_CONFIG["tuning"].suggest_mapping()


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
BASIC_PITCHES = {
    "F": (6, -4),
    "C": (4, -3),
    "G": (3, -2),
    "D": (1, -1),
    "a": (0, 0),
    "E": (-2, 1),
    "B": (-3, 2),
}
REFERENCE_OCTAVE = 4


def parse_pitch(token, inflections):
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
    result[0] += AUGMENTED_INFLECTION[0] * sharp
    result[1] += AUGMENTED_INFLECTION[1] * sharp

    separated = separate_by_arrows(token)

    for arrow_token in separated[1:]:
        arrows = 1
        if len(arrow_token) > 1:
            arrows = int(arrow_token[1:])
        result += inflections[arrow_token[0]]*arrows

    basic_pitch = BASIC_PITCHES[letter]

    result[0] += octave - REFERENCE_OCTAVE + basic_pitch[0]
    result[1] += basic_pitch[1]

    return result


def parse_interval(token, inflections, edn_divisions, edn_divided, return_root_degree=False):
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

    while token[0] == "c":
        pitch[0] += 1
        token = token[1:]

    root_degree = 1
    if "/" in token:
        maybe_token, degree_token = token.rsplit("/", 1)
        if not maybe_token.isdigit():  # Not a simple fraction
            token = maybe_token
            root_degree = int(degree_token)

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
            steps = Fraction(step_spec[0])
            if len(step_spec) >= 2:
                divisions = Fraction(step_spec[1])
            if len(step_spec) == 3:
                divided = Fraction(step_spec[2])
            pitch[E_INDEX] = float(steps) / float(divisions) * log(float(divided))
        else:
            pitch += parse_fraction(token)
    elif token[0] in INTERVAL_QUALITIES:
        pitch += parse_arrows(token, inflections)
    elif token[0] in BASIC_PITCHES:
        if direction is not None:
            raise ParsingError("Signed absolute pitch")
        pitch += parse_pitch(token, inflections)
        absolute = True

    if direction is not None:
        pitch *= direction

    if return_root_degree:
        return pitch, absolute, root_degree
    return pitch / root_degree, absolute


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


def comma_reduce_pattern(pattern, comma_list, persistence, cache=None):
    if cache is None:
        cache = {}
    if isinstance(pattern, Note):
        pattern.pitch = comma_reduce(pattern.pitch, comma_list, persistence, cache)
    if isinstance(pattern, Pattern):
        for subpattern in pattern:
            comma_reduce_pattern(subpattern, comma_list, persistence, cache)


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
                    if token.is_end() or token.value == TRACK_START:
                        raise ParsingError('Missing ":|"')
                    self.repeated_section.append(token)
                else:
                    return token

    @property
    def done(self):
        return self.lexer.done and not self.repeated_section


ARTICULATIONS = {
    ".": Fraction(1, 2),  # Staccato
    "_": Fraction(1),  # Tenuto
    ";": Fraction(9, 10),  # Normal
}


DYNAMICS = {
    "ppp": Fraction(1, 8),
    "pp": Fraction(1, 4),
    "p": Fraction(1, 3),
    "mp": Fraction(1, 2),
    "mf": Fraction(2, 3),
    "f": Fraction(3, 4),
    "ff": Fraction(7, 8),
    "fff": Fraction(1),
}


def parse_track(lexer, default_config):
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
    config.update(default_config)
    config["tuning"] = config["tuning"].copy()
    config["tempo"] = config["tempo"].copy()
    config["flags"] = list(config["flags"])
    edn_divisions = config["tuning"].edn_divisions
    edn_divided = config["tuning"].edn_divided
    current_notation = config["N"]
    base_frequency = None
    comma_list = None
    subgroup = None
    constraints = None
    max_polyphony = None

    for token_obj in lexer:
        if token_obj.is_end():
            break
        token = token_obj.value
        if token == TRACK_START:
            break

        if token in CONFIGS:
            config_key = token[:-1]
            config_mode = True
            continue

        if config_mode:
            if config_key == "a":
                base_frequency = float(token)
            if config_key == "T":
                comma_list, subgroup = TEMPERAMENTS[token.strip()]
                subgroup = subgroup.split(".")
            if config_key == "CL":
                comma_list = [comma.strip() for comma in token.split(",")]
            if config_key == "SG":
                subgroup = [basis_fraction.strip() for basis_fraction in token.split(".")]
            if config_key == "C":
                constraints = [constraint.strip() for constraint in token.split(",")]
            if config_key == "CRD":
                config[config_key] = int(token)
            if config_key == "WF":
                config[config_key] = token.strip()
            if config_key == "L":
                config["tempo"].beat_unit = Fraction(token)
            if config_key == "Q":
                unit, bpm = token.split("=")
                config["tempo"].tempo_unit = Fraction(unit)
                config["tempo"].tempo_duration = Fraction(60) / Fraction(bpm)
            if config_key == "G":
                span_token, pattern_token = token.split("=")
                config["tempo"].groove_span = Fraction(span_token)
                config["tempo"].groove_pattern = list(map(Fraction, pattern_token.split(" ")))
            if config_key == "V":
                track_volume = TrackVolume(Fraction(token), time)
                pattern.append(track_volume)
                config[config_key] = track_volume.volume
            if config_key in ("ED", "EDN"):
                if "unmapEDN" in config["flags"]:
                    config["flags"].remove("unmapEDN")
            if config_key == "ED":
                token = token.strip()
                warts = Counter()
                while token[-1].isalpha():
                    wart = token[-1].lower()
                    warts[ord(wart) - ord("a")] += 1
                    token = token[:-1]
                config["tuning"].warts = [warts[i] for i in range(len(PRIMES))]
                config["tuning"].edn_divisions = Fraction(token)
            if config_key == "EDN":
                config["tuning"].edn_divided = Fraction(token)
            if config_key == "N":
                current_notation = token.strip()
                config[config_key] = current_notation
            if config_key == "I":
                name = token.strip()
                program = GM_PROGRAMS.get(name)
                program_change = ProgramChange(name, program, time)
                pattern.append(program_change)
                config[config_key] = name
            if config_key == "MP":
                max_polyphony = int(token)
            if config_key == "F":
                config["flags"] = [flag.strip() for flag in token.split(",")]
            config_mode = False
            continue

        if time_mode:
            if token == "]":
                time_mode = False
            else:
                duration_token = token
                time_token = ""
                time -= pattern[-1].duration
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
            stack.append((pattern, time))
            pattern = Pattern([], time)
            time = Fraction(0)
        elif token == ")":
            subpattern = pattern
            pattern, time = stack.pop()
            pattern.append(subpattern)
            time += subpattern.duration
        elif token == "[":
            time_mode = True
        elif token == "]":
            raise ParsingError('Unmatched "]"')
        elif token == "&":
            transposed_pattern = pattern.pop()
        elif token == ",":
            time -= pattern[-1].duration
        elif token in ARTICULATIONS:
            articulation = Articulation(ARTICULATIONS[token], time)
            pattern.append(articulation)
        elif token in DYNAMICS:
            dynamic = Dynamic(DYNAMICS[token], time)
            pattern.append(dynamic)
        elif token in ("z", "Z"):
            rest = Rest((token=="Z"), time)
            pattern.append(rest)
            time += rest.duration
        elif token == "T":
            timestamp = time
        elif token == "|>":
            playhead = Playhead(time)
            pattern.append(playhead)
        elif token == ">|":
            playstop = Playstop(time)
            pattern.append(playstop)
        elif token.startswith('"'):
            message = UserMessage(token[1:], time)
            pattern.append(message)
        elif current_notation == "percussion":
            index, name = PERCUSSION_SHORTHANDS[token]
            percussion = Percussion(name, index, time)
            pattern.append(percussion)
            time += percussion.duration
        elif current_notation == "hewmp":
            if token.startswith("=") or ":" in token or ";" in token:
                if token_obj.whitespace or not token.startswith("="):
                    subpattern_time = time
                    subpattern_duration = Fraction(1)
                else:
                    replaced = pattern.pop()
                    subpattern_time = replaced.time
                    subpattern_duration = replaced.duration
                if token.startswith("="):
                    token = token[1:]
                subpattern = parse_chord(token, current_pitch, DEFAULT_INFLECTIONS, edn_divisions, edn_divided)
                subpattern.time = subpattern_time
                subpattern.duration = subpattern_duration
                pattern.append(subpattern)
            else:
                floaty = False
                if token.startswith("~"):
                    floaty = True
                    token = token[1:]
                interval, absolute = parse_interval(token, DEFAULT_INFLECTIONS, edn_divisions, edn_divided)

                if transposed_pattern:
                    if absolute:
                        raise ParsingError("Absolute transposition")
                    transposed_pattern.transpose(interval)
                    pattern.append(transposed_pattern)
                    transposed_pattern = None
                    if not floaty:
                        current_pitch += interval
                else:
                    if absolute:
                        current_pitch = zero_pitch()
                    pitch = current_pitch + interval
                    if not floaty:
                        current_pitch = pitch
                    note = Note(pitch, time)
                    pattern.append(note)
                    time += note.duration

    pattern.insert(0, Articulation(ARTICULATIONS[";"]))
    pattern.insert(0, Dynamic(DYNAMICS["mf"]))

    pattern.insert(0, config["tempo"])

    if base_frequency is not None:
        config["tuning"].base_frequency = base_frequency
    if subgroup is not None:
        config["tuning"].subgroup = [parse_interval(basis_vector, DEFAULT_INFLECTIONS, 12, 2)[0] for basis_vector in subgroup]
    if comma_list is not None:
        config["tuning"].comma_list = [parse_interval(comma, DEFAULT_INFLECTIONS, 12, 2)[0] for comma in comma_list]
    if constraints is not None:
        config["tuning"].constraints = [parse_interval(constraint, DEFAULT_INFLECTIONS, 12, 2)[0] for constraint in constraints]

    if "unmapEDN" in config["flags"]:
        config["tuning"].warts = None
    config["tuning"].suggest_mapping()
    pattern.insert(0, config["tuning"])

    pattern.duration = pattern.logical_duration

    if "CR" in config["flags"]:
        comma_reduce_pattern(pattern, comma_list, config["CRD"])

    pattern.max_polyphony = max_polyphony
    return pattern, config


def parse_file(file):
    if not file.seekable():
        file = StringIO(file.read())
    lexer = RepeatExpander(Lexer(file))
    global_track, global_config = parse_track(lexer, DEFAULT_CONFIG)
    results = [global_track]
    while not lexer.done:
        pattern, _ = parse_track(lexer, global_config)
        results.append(pattern)
    return results


def parse_text(text):
    return parse_file(StringIO(text))


# TODO: Simplify across tracks
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

        if event["type"] == "tuning":
            event["suggestedMapping"] = simplify(event["suggestedMapping"])

    return semantic, events


def _notate_fractions_chord(pattern):
    pitches = []
    for note in pattern:
        pitches.append(note.pitch)
    root_fraction = notate_fraction(pattern[0].pitch, PRIMES, E_INDEX, HZ_INDEX, RAD_INDEX)
    chord = notate_otonal_utonal(pitches, PRIMES)
    return "@{}={}".format(root_fraction, chord)


def _notate_fractions_pitch(pitch):
    return "@{}".format(notate_fraction(pitch, PRIMES, E_INDEX, HZ_INDEX, RAD_INDEX))


def _notate_absolute_chord(pattern, inflections):
    pitches = []
    for note in pattern:
        pitches.append(note.pitch)
    pitches = [notate_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX) for pitch in pitches]
    return "({})".format(",".join(pitches))


def _notate_absolute_pitch(pitch, inflections):
    return notate_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)


# TODO: Notate tracks
def notate_pattern(pattern, _notate_chord, _notate_pitch, main=False, absolute_time=False):
    if isinstance(pattern, Articulation):
        for symbol, value in ARTICULATIONS.items():
            if value == pattern.gate_ratio:
                return symbol
        raise ValueError("Innotable articulation")
    if isinstance(pattern, Dynamic):
        for symbol, value in DYNAMICS.items():
            if value == pattern.velocity:
                return symbol
        raise ValueError("Innotable dynamic")
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
            return _notate_chord(pattern) + suffix
        subnotations = []
        previous_time = None
        local_time = Fraction(0)
        for subpattern in pattern:
            force_notate = False
            if isinstance(subpattern, Articulation):
                force_notate = True
                if main and subpattern.time == 0 and subpattern.gate_ratio == ARTICULATIONS[";"]:
                    force_notate = False
            if isinstance(subpattern, Dynamic):
                force_notate = True
                if main and subpattern.time == 0 and subpattern.velocity == DYNAMICS["mf"]:
                    force_notate = False
            if subpattern.duration == 0 and not force_notate:
                continue
            local_absolute_time = False
            if subpattern.time != local_time:
                if subpattern.time == previous_time:
                    subnotations.append(",")
                else:
                    local_absolute_time = True
                local_time = subpattern.time
            subnotations.append(notate_pattern(subpattern, _notate_chord, _notate_pitch, absolute_time=local_absolute_time))
            previous_time = local_time
            local_time += subpattern.duration
        if main:
            return " ".join(filter(None, subnotations))
        return "(" + " ".join(filter(None, subnotations)) + ")" + suffix
    if isinstance(pattern, Note):
        return _notate_pitch(pattern.pitch) + suffix
    if isinstance(pattern, Rest):
        if pattern.emit:
            return "Z{}".format(suffix)
        return "z{}".format(suffix)

    return ""


FREQ_A4 = 440
INDEX_A4 = 69
MIDI_STEP = 2**(1/12)

def freq_to_midi(frequency, pitch_bend_depth):
    ratio = frequency / FREQ_A4
    steps = log(ratio) / log(MIDI_STEP)
    steps += INDEX_A4
    index = int(round(steps))
    bend = steps - index
    if bend < 0:
        bend = int(round(8192*bend/pitch_bend_depth))
    else:
        bend = int(round(8191*bend/pitch_bend_depth))
    return index, bend


def save_tracks_as_midi(file, tracks, pitch_bend_depth=2, reserve_channel_10=True, transpose=0, resolution=960):
    """
    Save tracks as a midi file with per-channel pitch-bend for microtones.

    Assumes that A4 is in standard tuning 440Hz.
    """
    midi = mido.MidiFile()
    channel_offset = 0
    for pattern in tracks:
        if pattern.duration <= 0:
            continue
        track = mido.MidiTrack()
        midi.tracks.append(track)

        data = pattern.to_json()
        base_frequency = None
        mapping = None
        velocity = 85
        events = []
        time_offset = 0
        for event in data["events"]:
            if event["type"] == "tuning":
                base_frequency = event["baseFrequency"]
                mapping = event["suggestedMapping"]
            if event["type"] == "dynamic":
                velocity = int(round(float(127 * Fraction(event["velocity"]))))
            if event["type"] in ("note", "percussion", "programChange") or event.get("subtype") == "controlChange":
                time = int(round(resolution * event["realtime"]))
            if event["type"] == "note":
                frequency = base_frequency*exp(dot(mapping, event["pitch"])) + event["pitch"][HZ_INDEX]
                events.append((time, event, frequency, velocity))
            if event["type"] == "percussion":
                events.append((time, event, None, velocity))
            if event["type"] == "programChange" or event.get("subtype") == "controlChange":
                change_time = time - 1
                if change_time < 0:
                    time_offset = -change_time
                events.append((change_time, event, None, None))
        presorted = events
        events = []
        channel = channel_offset
        key = lambda t: (t[0], t[2], t[3])
        for time, event, frequency, velocity in sorted(presorted, key=key):
            if event["type"] in ("note", "percussion"):
                duration = int(round(resolution * event["realGateLength"]))
                if duration <= 0:
                    continue
            if event["type"] == "note":
                index, bend = freq_to_midi(frequency, pitch_bend_depth)
                index += transpose
                channel_ = channel
                if reserve_channel_10 and channel >= 9:
                    channel_ += 1
                events.append((time, "note_on", index, bend, velocity, channel_))
                events.append((time + duration, "note_off", index, bend, velocity, channel_))
                channel = ((channel - channel_offset + 1) % pattern.max_polyphony) + channel_offset
            if event["type"] == "percussion":
                index = event["index"]
                if reserve_channel_10:
                    channel_ = 9
                else:
                    channel_ = channel
                    channel = ((channel - channel_offset + 1) % pattern.max_polyphony) + channel_offset
                events.append((time, "note_on", index, None, velocity, channel_))
                events.append((time + duration, "note_off", index, None, velocity, channel_))
            if event["type"] == "programChange":
                events.append((time, "program_change", event["program"], None, None, None))
            if event.get("subtype") == "controlChange":
                events.append((time, "control_change", event["control"], None, event["value"], None))

        current_time = 0
        for event in sorted(events):
            time, msg_type, index, bend, velocity, channel = event
            time += time_offset
            if msg_type == "program_change":
                for ch in range(pattern.max_polyphony):
                    ch += channel_offset
                    if reserve_channel_10 and ch >= 9:
                        ch += 1
                    message = mido.Message(msg_type, program=index, channel=ch, time=(time - current_time))
                    track.append(message)
                    current_time = time
            elif msg_type == "control_change":
                for ch in range(pattern.max_polyphony):
                    ch += channel_offset
                    if reserve_channel_10 and ch >= 9:
                        ch += 1
                    message = mido.Message(msg_type, control=index, value=velocity, channel=ch, time=(time - current_time))
                    track.append(message)
                    current_time = time
            else:
                if msg_type == "note_on" and bend is not None:
                    message = mido.Message("pitchwheel", pitch=bend, channel=channel, time=(time - current_time))
                    track.append(message)
                    current_time = time
                message = mido.Message(msg_type, note=index, channel=channel, velocity=velocity, time=(time - current_time))
                track.append(message)
                current_time = time
        channel_offset += pattern.max_polyphony
    midi.save(file=file)


if __name__ == "__main__":
    import argparse
    import sys
    import json

    parser = argparse.ArgumentParser(description='Parse input file (or stdin) in HEWMP notation and output JSON to file (or stdout)')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('--simplify', action='store_true')
    parser.add_argument('--fractional', action='store_true')
    parser.add_argument('--absolute', action='store_true')
    parser.add_argument('--midi', action='store_true')
    parser.add_argument('--pitch-bend-depth', type=int, default=2)
    parser.add_argument('--override-channel-10', action='store_true')
    parser.add_argument('--midi-transpose', type=int, default=0)
    args = parser.parse_args()

    patterns = parse_file(args.infile)
    if args.infile is not sys.stdin:
        args.infile.close()

    if args.fractional:
        args.outfile.write(notate_pattern(pattern, _notate_fractions_chord, _notate_fractions_pitch, True))
    elif args.absolute:
        inflections = reverse_inflections(DEFAULT_INFLECTIONS)
        _chord = lambda pattern: _notate_absolute_chord(pattern, inflections)
        _pitch = lambda pattern: _notate_absolute_pitch(pattern, inflections)
        args.outfile.write(notate_pattern(pattern, _chord, _pitch, True))
    elif args.midi or args.midi_edn or args.midi128:
        if mido is None:
            raise ValueError("Missing mido package")
        if args.outfile is sys.stdout:
            outfile = args.outfile
        else:
            filename = args.outfile.name
            args.outfile.close()
            outfile = open(filename, "wb")
        if args.midi:
            save_tracks_as_midi(outfile, patterns, args.pitch_bend_depth, not args.override_channel_10, args.midi_transpose)
    else:
        semantic = SEMANTIC
        result = {
            "semantic": SEMANTIC,
            "tracks": [],
        }
        for pattern in patterns:
            result["tracks"].append(pattern.to_json())
        if args.simplify:
            semantic, events = simplify_events(data["events"])
            data["events"] = events
        json.dump(result, args.outfile)

    if args.outfile is not sys.stdout:
        args.outfile.close()
    else:
        args.outfile.write("\n")
