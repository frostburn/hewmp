# coding: utf-8
from io import StringIO
from collections import Counter, defaultdict
try:
    import mido
except ImportError:
    mido = None
from fractions import Fraction
from .lexer import Lexer, CONFIGS, TRACK_START
from .extra_chords import EXTRA_CHORDS
from .chord_parser import expand_chord, separate_by_arrows
from .temperaments import TEMPERAMENTS, EQUAL_TEMPERAMENTS
from .notation import tokenize_fraction, tokenize_otonal_utonal, tokenize_pitch, reverse_inflections
from .percussion import PERCUSSION_SHORTHANDS
from .gm_programs import GM_PROGRAMS
from .rhythm import sequence_to_time_duration, euclidean_rhythm, pergen_rhythm, rotate_sequence, concatenated_geometric_rhythm, concatenated_arithmetic_rhythm, concatenated_harmonic_rhythm
from .rhythm import geometric_rhythm, harmonic_rhythm, sigmoid_rhythm
from .event import *
from .color import parse_interval as parse_color_interval, UNICODE_EXPONENTS
from .color import expand_chord as expand_color_chord
from .pythagoras import INTERVAL_QUALITIES, PITCH_LETTERS
from . import pythagoras
from .monzo import PRIMES, SemiMonzo, et_to_semimonzo
from .monzo import Interval as SemiInterval
from .monzo import Pitch as SemiPitch
from . import ups_and_downs
from .arrow import SignedArrow, SIGN_BY_ARROW
from . import orgone
from . import semaphore
from . import preed
from . import runic
from . import lambda_bp
from .temperament import infer_subgroup


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
    "n": [-5, 6, 0, 0, 0, 0, 0, 0, -1],
    "U": [-8, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    "D": [8, -2, 0, 0, 0, 0, 0, 0, 0, -1],
    "M": [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1],
    "W": [-5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
}
ARROWS = ""

for key, value in list(DEFAULT_INFLECTIONS.items()):
    ARROWS += key
    DEFAULT_INFLECTIONS[key] = array(value + [0] * (len(PRIMES) - len(value)))


TEMPORAL_MINI_LANGUAGE = ".!?%"  # Chainable tokens


DEFAULT_SIGNED_INFLECTIONS = {}
for arrow in SignedArrow:
    DEFAULT_SIGNED_INFLECTIONS[arrow] = DEFAULT_INFLECTIONS[arrow.value[0]]


class Interval:
    absolute = False
    def __init__(self, spine, arrows, inflections):
        self.spine = spine
        self.arrows = arrows
        self.inflections = inflections

    @property
    def interval_class(self):
        return self.spine.interval_class

    def monzo(self):
        result = self.spine.monzo()
        for arrow, count in self.arrows.items():
            result += self.inflections[arrow] * count
        return result


class Pitch:
    absolute = True
    def __init__(self, spine, arrows, inflections):
        self.spine = spine
        self.arrows = arrows
        self.inflections = inflections

    def monzo(self):
        result = self.spine.monzo()
        for arrow, count in self.arrows.items():
            result += self.inflections[arrow] * count
        return result


class MonzoInterval:
    def __init__(self, value, absolute=False):
        self.value = value
        self.absolute = absolute

    def monzo(self):
        return self.value


class ParsedInterval:
    def __init__(self, base, octaves=0, ups=0, root=1, exponent=1, absolute=False, up_inflection=None, offset=None):
        self.base = base
        self.octaves = octaves
        self.ups = ups
        self.root = root
        self.exponent = exponent
        self.up_inflection = up_inflection
        self._absolute = absolute
        self.offset = offset

    @property
    def interval_class(self):
        return getattr(self.base, "interval_class", None)

    def value(self):
        if not isinstance(self.base, SemiInterval):
            result = SemiInterval(SemiMonzo(self.base.monzo()))
        else:
            result = self.base.copy()
        result.monzo.vector[0] += self.octaves
        result += self.up_inflection * self.ups
        result = result / self.root * self.exponent
        if self.offset is not None:
            result += self.offset
        if self.absolute:
            return SemiPitch() + result
        return result

    @property
    def absolute(self):
        return self.base.absolute or self._absolute

    @absolute.setter
    def absolute(self, value):
        self._absolute = value


def parse_warts(token, index=0):
    token = token.lower()
    if "d" in token:
        token, divided_token = token.rsplit("d", 1)
        if divided_token == "o":
            et_divided = 2
        elif divided_token == "t":
            et_divided = 3
        elif divided_token == "p":
            et_divided = 5
        elif not divided_token:
            et_divided = 2
            token = "de"
        else:
            et_divided = int(divided_token)
        token = token[:-1]
    else:
        et_divided = 2
    warts = Counter()
    wart_str = ""
    while token[-1].isalpha():
        wart = token[-1].lower()
        wart_str += wart
        warts[ord(wart) - ord("a")] += 1
        token = token[:-1]
    et_divisions = int(token)
    return et_divisions, et_divided, warts, wart_str


def sync_playheads(patterns):
    start_universal_time = None
    end_universal_time = None
    tempi = []
    end_times = []
    for pattern in patterns:
        start_time = None
        end_time = None
        tempo = None
        for event in pattern.flatten():
            if isinstance(event, Playstop):
                end_time = event.end_time
            elif isinstance(event, Playhead):
                start_time = event.time
            elif isinstance(event, Tempo):
                tempo = event
        tempi.append(tempo)
        end_times.append(end_time)
        if start_time is not None:
            universal = start_time * tempo.beat_unit
            if start_universal_time is None or universal > start_universal_time:
                start_universal_time = universal
    for tempo, end_time in zip(tempi, end_times):
        if end_time is not None:
            universal = end_time * tempo.beat_unit
            if start_universal_time is None or universal > start_universal_time:
                if end_universal_time is None or universal < end_universal_time:
                    end_universal_time = universal
    result = []
    for tempo in tempi:
        start_time = None
        end_time = None
        if start_universal_time is not None:
            start_time = start_universal_time / tempo.beat_unit
        if end_universal_time is not None:
            end_time = end_universal_time / tempo.beat_unit
        result.append((start_time, end_time))
    return result


DEFAULT_CONFIG = {
    "tuning": Tuning(440.0, (), (), (), Fraction(12), Fraction(2), None),  # warts is None so it's JI
    "tempo": Tempo(Fraction(1, 4), Fraction(1, 2), Fraction(1, 4)),
    "track_volume": TrackVolume(Fraction(1)),
    "program_change": None,
    "CRD": 5,
    "N": "hewmp",
    "flags": ("unmapET",),  # default to just intonation
    "SG": "auto",
}

DEFAULT_CONFIG["tuning"].suggest_mapping()


class ParsingError(Exception):
    pass


def parse_signed_arrows(token):
    separated = separate_by_arrows(token)
    arrows = Counter()
    for arrow_token in separated[1:]:
        count = 1
        if len(arrow_token) > 1:
            count = int(arrow_token[1:])
        sign, arrow = SIGN_BY_ARROW[arrow_token[0]]
        arrows[arrow] += sign * count
    return arrows


def parse_interval(token, inflections, parse_spine=pythagoras.Interval.parse):
    token, spine = parse_spine(token)
    arrows = parse_signed_arrows(token)
    return Interval(spine, arrows, inflections)


def parse_pitch(token, inflections, parse_spine=pythagoras.Pitch.parse):
    token, spine = parse_spine(token)
    arrows = parse_signed_arrows(token)
    return Pitch(spine, arrows, inflections)


class IntervalParser:
    def __init__(self, inflections=None, et_divisions=Fraction(12), et_divided=Fraction(2), warts=""):
        if inflections is None:
            inflections = {
                "hewmp": DEFAULT_SIGNED_INFLECTIONS,
                "orgone": orgone.INFLECTIONS,
                "semaphore": semaphore.INFLECTIONS,
                "preed": preed.INFLECTIONS,
                "runic": runic.INFLECTIONS,
                "lambda": lambda_bp.INFLECTIONS,
            }
        self.inflections = inflections
        self.et_divisions = et_divisions
        self.et_divided = et_divided
        self.warts = warts
        self.offset = SemiInterval()
        self.comma_list = None
        self.persistence = 5
        self.up_down_inflection = SemiInterval()
        self.up_down_inflection.monzo.vector[0] = Fraction(1, 2)  # Default to half-octave

    interval_spines = {
        "hewmp": pythagoras.Interval.parse,
        "orgone": orgone.Interval.parse,
        "semaphore": semaphore.Interval.parse,
        "preed": preed.Interval.parse,
        "runic": runic.Interval.parse,
        "lambda": lambda_bp.Interval.parse,
    }

    pitch_spines = {
        "hewmp": pythagoras.Pitch.parse,
        "orgone": orgone.Pitch.parse,
        "semaphore": semaphore.Pitch.parse,
        "preed": preed.Pitch.parse,
        "runic": runic.Pitch.parse,
        "lambda": lambda_bp.Pitch.parse,
    }

    def calculate_up_down(self):
        wart_str = "{}{}ED{}".format(self.et_divisions, self.warts, self.et_divided)
        self.up_down_inflection = SemiInterval()
        if wart_str in ups_and_downs.ARROW_INFLECTIONS:
            base = ups_and_downs.ARROW_INFLECTIONS[wart_str]
            self.up_down_inflection.monzo.vector[:len(base)] = base
        else:
            self.up_down_inflection = SemiInterval(et_to_semimonzo(1, self.et_divisions, self.et_divided))

    def set_base_pitch(self, token, notation="hewmp"):
        if token[0] in PITCH_LETTERS:
            pitch = parse_pitch(token, self.inflections[notation], self.pitch_spines[notation])
            self.offset = SemiInterval(-pitch.monzo())
        else:
            color = parse_color_interval(token)
            if color.absolute:
                self.offset = SemiInterval(-color.monzo())
            else:
                raise ParsingError("Unrecognized absolute pitch {}".format(token))

    def parse(self, token, notation="hewmp"):
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

        octaves = 0

        while token[0] == "c":
            octaves += 1
            token = token[1:]

        while token[0] == "`":
            octaves -= 1
            token = token[1:]

        has_up_down = (token[0] in "^v")
        ups = 0
        while token[0] == "^":
            ups += 1
            token = token[1:]
        while token[0] == "v":
            ups -= 1
            token = token[1:]
        if has_up_down and token[0].isdigit():
            token = "w" + token

        exponent_degree = 1
        root_degree = 1
        if "/" in token:
            maybe_token, degree_token = token.rsplit("/", 1)
            if not maybe_token.isdigit():  # Not a simple fraction
                token = maybe_token
                if "*" in degree_token:
                    degree_token, exponent_token = degree_token.split("*", 1)
                    exponent_degree = int(exponent_token)
                root_degree = int(degree_token)

        # Quick non-exhaustive check for color notation
        is_colored = (
            "o" in token or "u" in token or (
                (token[0] == "L" or token[0] == "s") and (
                    not token[1].isdigit() or token[1] in UNICODE_EXPONENTS
                )
            )
        )

        if direction is not None:
            exponent_degree *= direction
        result = ParsedInterval(None, octaves, ups, root_degree, exponent_degree, absolute, self.up_down_inflection)

        if token[0].isdigit() and not is_colored:
            interval = SemiInterval()
            if token.endswith("c"):
                interval.monzo.nats = float(token[:-1])/1200*log(2)
            elif token.endswith("Hz"):
                interval.frequency_delta = float(token[:-2])
            elif token.endswith("deg"):
                interval.phase_delta = float(token[:-3]) / 180 * pi
            elif "\\" in token:
                divisions = self.et_divisions
                divided = self.et_divided
                step_spec = token.split("\\")
                steps = Fraction(step_spec[0])
                if len(step_spec) >= 2 and step_spec[1]:
                    divisions = Fraction(step_spec[1])
                if len(step_spec) == 3:
                    divided = Fraction(step_spec[2])
                interval.monzo = et_to_semimonzo(steps, divisions, divided)
            else:
                interval.monzo = SemiMonzo(Fraction(token))
            result.base = interval
        elif token[0] in INTERVAL_QUALITIES:
            interval = parse_interval(token, self.inflections[notation], self.interval_spines[notation])
            result.base = interval
        elif token[0] in PITCH_LETTERS:
            if direction is not None:
                raise ParsingError("Signed absolute pitch")
            pitch = parse_pitch(token, self.inflections[notation], self.pitch_spines[notation])
            result.base = pitch
            result.offset = self.offset
        else:
            color = parse_color_interval(token)
            if color.absolute:
                result.offset = self.offset
            result.base = color

        return result


def parse_otonal(token, interval_parser):
    subtokens = token.split(":")
    intervals = []
    for subtoken in subtokens:
        interval = interval_parser.parse(subtoken)
        if interval.absolute:
            raise ParsingError("Otonal chord using absolute pitches")
        intervals.append(interval.value())
    root = intervals[0]
    for i in range(len(intervals)):
        intervals[i] = intervals[i] - root
    return Pattern([Note(interval) for interval in intervals], logical_duration=1)


def parse_utonal(token, interval_parser):
    subtokens = token.split(";")
    intervals = []
    for subtoken in subtokens:
        interval = interval_parser.parse(subtoken)
        if interval.absolute:
            raise ParsingError("Utonal chord using absolute pitches")
        intervals.append(interval.value())
    root = intervals[0]
    for i in range(len(intervals)):
        intervals[i] = root - intervals[i]
    return Pattern([Note(interval) for interval in intervals], logical_duration=1)


def parse_chord(token, transposition, interval_parser):
    notation = "hewmp"
    inversion = 0
    voicing = None
    interval_classes = []
    if "_" in token:
        token, voicing_token = token.split("_")
        if voicing_token.isdigit():
            inversion = int(voicing_token)
        elif "R" in voicing_token:
            root_index = voicing_token.index("R")
            voicing = defaultdict(list)
            voicing[1].append(0)

            octave = 0
            last = 1
            for tone in voicing_token[root_index+1:]:
                tone = int(tone)
                if tone <= last:
                    octave += 1
                last = tone
                voicing[tone].append(octave)

            octave = 0
            last = 1
            for tone in reversed(voicing_token[:root_index]):
                tone = int(tone)
                if tone >= last:
                    octave -= 1
                last = tone
                voicing[tone].append(octave)
        else:
            raise ParsingError("Unrecognized voicing {}".format(voicing_token))

    if ":" in token:
        result = parse_otonal(token, interval_parser)
        result.transpose(transposition)
    elif ";" in token:
        result = parse_utonal(token, interval_parser)
        result.transpose(transposition)
    else:
        if token in EXTRA_CHORDS:
            subtokens = EXTRA_CHORDS[token]
        elif token in orgone.EXTRA_CHORDS:
            subtokens = orgone.EXTRA_CHORDS[token]
            notation = "orgone"
        elif token in semaphore.EXTRA_CHORDS:
            subtokens = semaphore.EXTRA_CHORDS[token]
            notation = "semaphore"
        elif token in preed.EXTRA_CHORDS:
            subtokens = preed.EXTRA_CHORDS[token]
            notation = "preed"
        elif token in runic.EXTRA_CHORDS:
            subtokens = runic.EXTRA_CHORDS[token]
            notation = "runic"
        # TODO: Lambda chords
        else:
            subtokens = expand_color_chord(token)
            if subtokens is None:
                subtokens, notation = expand_chord(token)
        result = Pattern(logical_duration=1)
        for subtoken in subtokens:
            interval = interval_parser.parse(subtoken, notation)
            pitch = interval.value()
            if pitch.absolute:
                result.append(Note(pitch))
            else:
                result.append(Note(pitch + transposition))
            interval_classes.append(interval.interval_class)
    for i in range(inversion):
        result[i].pitch.monzo.vector[0] += 1
    if inversion:
        for i in range(len(result)):  #pylint: disable=consider-using-enumerate
            result[i].pitch.monzo.vector[0] -= 1
    if voicing is not None:
        for tone, octaves in voicing.items():
            pitch = result[interval_classes.index(tone)].pitch.copy()
            for i, octave in enumerate(octaves):
                if i == 0:
                    result[interval_classes.index(tone)].pitch.monzo.vector[0] += octave
                else:
                    result.append(Note(pitch))
                    result[-1].pitch.monzo.vector[0] += octave

    return result


def comma_reduce_pattern(pattern, comma_list, persistence, cache=None):
    if cache is None:
        cache = {}
    if isinstance(pattern, Note):
        # TODO: Convert back to Fractions
        pattern.pitch.monzo.vector = comma_reduce(pattern.pitch.monzo.vector, comma_list, persistence, cache)
    if isinstance(pattern, Pattern):
        for subpattern in pattern:
            comma_reduce_pattern(subpattern, comma_list, persistence, cache)


def patternify(pattern):
    if not isinstance(pattern, Pattern):
        pattern = Pattern([pattern], time=pattern.time, duration=pattern.duration, logical_duration=pattern.duration)
        pattern[0].time = Fraction(0)
    return pattern


def parse_time(token):
    """
    Better version of Fraction() that can do multiplication
    """
    result = Fraction(1)
    for subtoken in token.split("*"):
        result *= Fraction(subtoken.strip())
    return result


class RepeatExpander:
    def __init__(self, lexer, max_repeats=None):
        self.lexer = lexer
        self.max_repeats = max_repeats

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
                    if self.max_repeats is not None and num_repeats > self.max_repeats:
                        raise ParsingError("Too many section repeats")
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
    "'": Fraction(1, 2),  # Staccato
    "_": Fraction(1),  # Tenuto
    ";": Fraction(9, 10),  # Normal
}


DYNAMICS = {
    "pppp": Fraction(1, 16),
    "ppp": Fraction(1, 8),
    "pp": Fraction(1, 4),
    "p": Fraction(1, 3),
    "mp": Fraction(1, 2),
    "mf": Fraction(2, 3),
    "f": Fraction(3, 4),
    "ff": Fraction(7, 8),
    "fff": Fraction(9, 10),
    "ffff": Fraction(1),
}


def parse_track(lexer, default_config, max_repeats=None):
    config_mode = False
    config_key = None
    time_mode = False
    repeat_mode = False
    pattern = Pattern()
    stack = []
    owner_pattern = None
    transposed_pattern = None
    concatenated_pattern = None
    add_concatenated_durations = None
    current_pitch = SemiPitch()
    timestamp = 0
    if "interval_parser" in default_config:
        interval_parser = default_config["interval_parser"]
    else:
        interval_parser = IntervalParser()

    config = {}
    config.update(default_config)
    config["tuning"] = config["tuning"].copy()
    config["tempo"] = config["tempo"].copy()
    config["flags"] = list(config["flags"])
    current_notation = "hewmp"
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
            if config_key == "BF":
                config["tuning"].base_frequency = float(token)
            if config_key == "BN":
                for subtoken in token.split(","):
                    interval_parser.set_base_pitch(subtoken.strip(), current_notation)
            if config_key == "T":
                tuning_name = token.strip()
                if tuning_name in TEMPERAMENTS:
                    comma_list, subgroup = TEMPERAMENTS[tuning_name]
                    subgroup = subgroup.split(".")
                    config["tuning"].subgroup = [interval_parser.parse(basis_vector).value().monzo.float_vector() for basis_vector in subgroup]
                    config["tuning"].comma_list = [interval_parser.parse(comma).value().monzo.float_vector() for comma in comma_list]
                else:
                    raise ParsingError("Unrecognized tuning '{}'".format(tuning_name))
            if config_key == "CL":
                comma_list = [comma.strip() for comma in token.split(",")]
                config["tuning"].comma_list = [interval_parser.parse(comma).value().monzo.float_vector() for comma in comma_list]
                if config["SG"] == "auto":
                    config["tuning"].subgroup = infer_subgroup(config["tuning"].comma_list)
            if config_key == "SG":
                subgroup = [basis_fraction.strip() for basis_fraction in token.split(".")]
                config["tuning"].subgroup = [interval_parser.parse(basis_vector).value().monzo.float_vector() for basis_vector in subgroup]
            if config_key == "C":
                constraints = [constraint.strip() for constraint in token.split(",")]
                config["tuning"].constraints = [interval_parser.parse(constraint).value().monzo.float_vector() for constraint in constraints]
            if config_key == "CRD":
                config[config_key] = int(token)
                interval_parser.persistence = int(token)
            if config_key == "L":
                config["tempo"].beat_unit = Fraction(token)
            if config_key == "Q":
                unit, bpm = token.split("=")
                config["tempo"].tempo_unit = Fraction(unit)
                config["tempo"].tempo_duration = Fraction(60) / Fraction(bpm)
            if config_key == "G":
                span_token, pattern_token = token.split("=")
                config["tempo"].groove_span = Fraction(span_token)
                config["tempo"].groove_pattern = list(map(Fraction, filter(None, pattern_token.split(" "))))
            if config_key == "V":
                track_volume = TrackVolume(Fraction(token), pattern.t)
                pattern.append(track_volume)
                config[config_key] = track_volume.volume
            if config_key == "ET":
                if "unmapET" in config["flags"]:
                    config["flags"].remove("unmapET")
                token = token.strip()
                if token in EQUAL_TEMPERAMENTS:
                    et_divisions, et_divided = EQUAL_TEMPERAMENTS[token]
                    warts = Counter()
                    wart_str = ""
                else:
                    et_divisions, et_divided, warts, wart_str = parse_warts(token)
                config["tuning"].warts = [warts[i] for i in range(len(PRIMES))]
                config["tuning"].et_divisions = et_divisions
                config["tuning"].et_divided = et_divided
                interval_parser.et_divisions = et_divisions
                interval_parser.et_divided = et_divided
                interval_parser.warts = wart_str
                interval_parser.calculate_up_down()
            if config_key == "N":
                current_notation = token.strip()
                if current_notation not in ["hewmp", "HEWMP", "orgone", "semaphore", "preed", "runic", "lambda", "percussion", "percussion!"]:
                    raise ParsingError("Unknown notation '{}'".format(current_notation))
                current_notation = current_notation.lower()
                config[config_key] = current_notation
                pattern.append(ContextChange(current_notation, pattern.t))
            if config_key == "I":
                name = token.strip()
                program = GM_PROGRAMS.get(name)
                program_change = ProgramChange(name, program, pattern.t)
                pattern.append(program_change)
                config[config_key] = name
            if config_key == "WF":
                name = token.strip()
                pattern.append(Waveform(name, pattern.t))
                config[config_key] = name
            if config_key == "ADSR":
                a, d, s, r = token.split(" ")
                a = Fraction(a)/1000
                d = Fraction(d)/1000
                s = Fraction(s)/100
                r = Fraction(r)/1000
                pattern.append(Envelope(a, d, s, r, pattern.t))
                config[config_key] = (a, d, s, r)
            if config_key == "MP":
                max_polyphony = int(token)
            if config_key == "F":
                config["flags"] = [flag.strip() for flag in token.split(",")]
                if "CR" in config["flags"]:
                    config["comma_reduction_cache"] = {}
            config_mode = False
            continue

        if time_mode:
            default = False
            if token == "]":
                time_mode = False
            elif token.startswith("*"):
                duration_token = token[1:]
                pattern.t -= pattern.last.duration
                pattern.last.duration *= parse_time(duration_token)
                pattern.t += pattern.last.duration
            elif token == "~":
                pattern.t -= pattern.last.duration
                pattern.last.duration = pattern.last.logical_duration  # TODO: Better error for Notes
                pattern.t += pattern.last.duration
            elif token.startswith("!"):
                pattern.t -= pattern.last.duration
                extension = parse_time(token[1:])
                pattern.last.extend_duration(extension)
                pattern.t += pattern.last.duration
            elif token.startswith("?") and len(token) > 1:
                extension = parse_time(token[1:])
                pattern.last.extend_duration(extension)
            elif token.startswith("@"):
                pattern.last.time = parse_time(token[1:])
                pattern.t = pattern.last.time
                pattern.t += pattern.last.duration
            elif token.lower().startswith("x"):
                pattern.last = patternify(pattern.last)
                pattern.t -= pattern.last.duration
                num_repeats = int(token[1:])
                if max_repeats is not None and num_repeats > max_repeats:
                    raise ParsingError("Too many repeats")
                pattern.last.repeat(num_repeats, affect_duration=(token.startswith("X")))
                pattern.t += pattern.last.duration
            elif isinstance(pattern.last, Pattern):
                if token == "R":
                    pattern.last.reverse_time()
                elif token == "r":
                    pattern.last.reverse_logic()
                elif "<" in token:
                    pattern.last.rotate_time(token.count("<"))
                elif ">" in token:
                    pattern.last.rotate_time(-token.count(">"))
                elif "v" in token:
                    pattern.last.rotate_rhythm(token.count("v"))
                elif "^" in token:
                    pattern.last.rotate_rhythm(-token.count("^"))
                elif token == "?":
                    pattern.last.stretch_subpatterns()
                elif token == "a" or "G" in token or "CA" in token or "H" in token or "E" in token or "S" in token:
                    num_onsets = len(pattern.last)

                    if "C" in token:
                        initial_token = token[:token.index("C")]
                        if initial_token:
                            initial = Fraction(initial_token)
                        else:
                            initial = Fraction(1)

                    if token == "a":
                        times_durations = [(i, 1) for i in range(num_onsets)]
                    elif "E" in token:
                        rotation_token = token[:token.index("E")]
                        num_beats = int(token[token.index("E")+1:])
                        rhythm = euclidean_rhythm(num_onsets, num_beats)
                        if rotation_token:
                            for _ in range(int(rotation_token)):
                                rhythm = rotate_sequence(rhythm)
                        times_durations = sequence_to_time_duration(rhythm)
                    elif "PG" in token:
                        period_token = token[token.index("G")+1:]
                        generator = Fraction(token[:token.index("P")])
                        if period_token:
                            period = Fraction(period_token)
                        else:
                            period = Fraction(1)
                        times_durations = pergen_rhythm(num_onsets, generator, period)
                    elif "CG" in token:
                        factor = Fraction(token[token.index("G")+1:])
                        times_durations = concatenated_geometric_rhythm(num_onsets, initial, factor)
                    elif "G" in token:
                        factor = Fraction(token[token.index("G")+1:])
                        initial_token = token[:token.index("G")]
                        if initial_token:
                            initial = Fraction(initial_token)
                        else:
                            initial = Fraction(1)
                        times_durations = geometric_rhythm(num_onsets, initial, factor)
                    elif "CA" in token:
                        delta_token = token[token.index("A")+1:]
                        if delta_token:
                            delta = Fraction(delta_token)
                        else:
                            delta = Fraction(1)
                        times_durations = concatenated_arithmetic_rhythm(num_onsets, initial, delta)
                    elif "CH" in token:
                        delta_token = token[token.index("H")+1:]
                        if delta_token:
                            delta = Fraction(delta_token)
                        else:
                            delta = Fraction(1)
                        times_durations = concatenated_harmonic_rhythm(num_onsets, initial, delta)
                    elif "H" in token:
                        delta_token = token[token.index("H")+1:]
                        initial_token = token[:token.index("H")]
                        if delta_token:
                            delta = Fraction(delta_token)
                        else:
                            delta = Fraction(1)
                        if initial_token:
                            initial = Fraction(initial_token)
                        else:
                            initial = Fraction(1)
                        times_durations = harmonic_rhythm(num_onsets, initial, delta)
                    elif "S" in token:
                        scale_token = token[token.index("S")+1:]
                        if scale_token:
                            scale = Fraction(scale_token)
                        else:
                            scale = Fraction(1)
                        bias_token = token[:token.index("S")]
                        if bias_token:
                            bias = Fraction(bias_token)
                        else:
                            bias = Fraction(0)
                        times_durations = sigmoid_rhythm(num_onsets, bias, scale)

                    for subpattern, td in zip(pattern.last, times_durations):
                        subpattern.time, subpattern.duration = td
                    pattern.last.logical_duration = pattern.last.last.end_time
                else:
                    default = True
            else:
                default = True
            if default:
                duration_token = token
                pattern.t -= pattern.last.duration
                pattern.last.duration = parse_time(duration_token)
                pattern.t += pattern.last.duration
            continue

        if token == "(":
            time = pattern.t
            stack.append(pattern)
            pattern = Pattern([], time)
        elif token == ")":
            subpattern = pattern
            pattern = stack.pop()
            if concatenated_pattern:
                subpattern = concatenated_pattern.concatenate(subpattern, add_concatenated_durations)
                concatenated_pattern = None
            pattern.append(subpattern)
            pattern.t += subpattern.duration
        elif token == "[":
            time_mode = True
        elif token == "]":
            raise ParsingError('Unmatched "]"')
        elif token == "{":
            if owner_pattern is not None:
                raise ParsingError('Nested "{"')
            owner_pattern = pattern
            pattern = Pattern()
        elif token == "}":
            owner_pattern.last.properties = pattern
            pattern = owner_pattern
            owner_pattern = None
        elif token == "&":
            transposed_pattern = pattern.pop()
        elif token == "+":
            concatenated_pattern = patternify(pattern.pop())
            add_concatenated_durations = True
            pattern.t -= concatenated_pattern.duration
        elif token == "=":
            concatenated_pattern = patternify(pattern.pop())
            add_concatenated_durations = False
            pattern.t -= concatenated_pattern.duration
        elif all(mt in TEMPORAL_MINI_LANGUAGE for mt in token):
            for mini_token in token:
                if mini_token == "%":
                    repeated_pattern = pattern.last_voiced.retime(pattern.t, 1)
                    pattern.append(repeated_pattern)
                    pattern.t += pattern.last.duration
                elif mini_token == ".":
                    pattern.append(Rest(pattern.t))
                    pattern.t += pattern.last.duration
                elif mini_token == "!":
                    pattern.last.extend_duration(1)
                    pattern.t += 1
                elif mini_token == "?":
                    pattern.last.extend_duration(1)
        elif token == ",":
            pattern.t -= pattern.last.duration
        elif token[0] in ARTICULATIONS:
            if len(token) == 1:
                value = ARTICULATIONS[token]
            else:
                value = Fraction(token[1:])
            pattern.append(Articulation(value, pattern.t))
        elif token[0] in ("p", "f") or token.startswith("mp") or token.startswith("mf"):
            dynamic_token = ""
            while token and token[0] in ("p", "f"):
                dynamic_token += token[0]
                token = token[1:]
            if token and token[0] == "m":
                dynamic_token = token[:2]
                token = token[2:]
            if token:
                value = Fraction(token)
            else:
                value = DYNAMICS[dynamic_token]
            pattern.append(Dynamic(value, pattern.t))
        elif token == "T":
            timestamp = pattern.t
        elif token == "@T":
            pattern.t = timestamp
        elif token == "\n":
            pattern.append(NewLine(token, pattern.t))
        elif token == "|":
            pattern.append(BarLine(token, pattern.t))
        elif token == "|>":
            pattern.append(Playhead(token, pattern.t))
        elif token == ">|":
            pattern.append(Playstop(token, pattern.t))
        elif token.startswith('"'):
            message = UserMessage(token[1:], pattern.t)
            pattern.append(message)
        elif current_notation in ("percussion", "percussion!"):
            if token in PERCUSSION_SHORTHANDS and current_notation == "percussion":
                index, name = PERCUSSION_SHORTHANDS[token]
                percussion = Percussion(name, index, time=pattern.t)
                pattern.append(percussion)
                pattern.t += percussion.duration
            else:
                for mini_token in token:
                    if mini_token in PERCUSSION_SHORTHANDS:
                        index, name = PERCUSSION_SHORTHANDS[mini_token]
                        percussion = Percussion(name, index, time=pattern.t)
                        pattern.append(percussion)
                        pattern.t += percussion.duration
                    elif mini_token == "%":
                        repeated_pattern = pattern.last_voiced.retime(pattern.t, 1)
                        pattern.append(repeated_pattern)
                        pattern.t += pattern.last.duration
                    elif mini_token == ".":
                        pattern.append(Rest(pattern.t))
                        pattern.t += pattern.last.duration
                    elif mini_token == "!":
                        pattern.last.extend_duration(1)
                        pattern.t += 1
                    elif mini_token == "?":
                        pattern.last.extend_duration(1)

        elif current_notation in ("hewmp", "orgone", "semaphore", "preed", "runic", "lambda"):
            if token.startswith("=") or ":" in token or ";" in token:
                if token_obj.whitespace or not token.startswith("=") or not pattern or isinstance(pattern[-1], NewLine):
                    subpattern_time = pattern.t
                    subpattern_duration = Fraction(1)
                    pattern.t += subpattern_duration
                    pitch = current_pitch
                else:
                    replaced = pattern.pop()
                    subpattern_time = replaced.time
                    subpattern_duration = replaced.duration
                    pitch = replaced.pitch
                if token.startswith("="):
                    token = token[1:]
                subpattern = parse_chord(token, pitch, interval_parser)
                subpattern.time = subpattern_time
                subpattern.duration = subpattern_duration
                pattern.append(subpattern)
                if concatenated_pattern:
                    subpattern = pattern.pop()
                    pattern.t -= subpattern.duration
                    subpattern = concatenated_pattern.concatenate(subpattern, add_concatenated_durations)
                    concatenated_pattern = None
                    pattern.append(subpattern)
                    pattern.t += subpattern.duration
            else:
                moves_root = False
                if token.startswith("~"):
                    moves_root = True
                    token = token[1:]
                interval = interval_parser.parse(token, current_notation).value()

                if transposed_pattern:
                    if interval.absolute:
                        raise ParsingError("Absolute transposition")
                    transposed_pattern.transpose(interval)
                    pattern.append(transposed_pattern)
                    transposed_pattern = None
                    if moves_root:
                        current_pitch += interval
                else:
                    if interval.absolute:
                        if moves_root:
                            raise ParsingError("Superfluous root move (~) with an absolute pitch")
                        current_pitch = interval
                        pitch = current_pitch
                    else:
                        pitch = current_pitch + interval
                        if moves_root:
                            current_pitch = pitch
                    note = Note(pitch, time=pattern.t)
                    pattern.append(note)
                    if "comma_reduction_cache" in config:  # TODO: Convert to Fractions
                        current_pitch.monzo.vector = comma_reduce(current_pitch.monzo.vector, config["tuning"].comma_list, persistence=config["CRD"], cache=config["comma_reduction_cache"])
                    pattern.t += note.duration

                if concatenated_pattern:
                    subpattern = patternify(pattern.pop())
                    pattern.t -= subpattern.duration
                    subpattern = concatenated_pattern.concatenate(subpattern, add_concatenated_durations)
                    concatenated_pattern = None
                    pattern.append(subpattern)
                    pattern.t += subpattern.duration

    pattern.insert(0, Articulation(ARTICULATIONS[";"]))
    pattern.insert(0, Dynamic(DYNAMICS["mf"]))

    pattern.insert(0, config["tempo"])

    if "unmapET" in config["flags"]:
        config["tuning"].warts = None
    config["tuning"].suggest_mapping()
    pattern.insert(0, config["tuning"])

    pattern.duration = pattern.logical_duration

    if max_polyphony is not None:
        pattern.max_polyphony = max_polyphony

    config["interval_parser"] = interval_parser
    return pattern, config


def parse_file(file, max_repeats=None):
    if not file.seekable():
        file = StringIO(file.read())
    lexer = RepeatExpander(Lexer(file), max_repeats=max_repeats)
    global_track, global_config = parse_track(lexer, DEFAULT_CONFIG, max_repeats=max_repeats)
    results = [global_track]
    while not lexer.done:
        pattern, _ = parse_track(lexer, global_config, max_repeats=max_repeats)
        results.append(pattern)
    return results, global_config


def parse_text(text, max_repeats=None):
    return parse_file(StringIO(text), max_repeats=max_repeats)


def realize(patterns):
    result = []
    for pattern, (start_time, end_time) in zip(patterns, sync_playheads(patterns)):
        result.append(pattern.realize(start_time=start_time, end_time=end_time))
    return result


def simplify_tracks(data):
    used = array([False] * len(PRIMES))

    for track in data["tracks"]:
        for event in track["events"]:
            if event["type"] == "note":
                for i, coord in enumerate(event["monzo"]):
                    if coord != 0:
                        used[i] = True

    def simplify(pitch):
        result = []
        for coord in array(pitch)[used]:
            if coord == int(coord):
                coord = int(coord)
            result.append(coord)
        return result

    for track in data["tracks"]:
        for event in track["events"]:
            if event["type"] == "note":
                event["monzo"] = simplify(event["monzo"])

            if event["type"] == "tuning":
                event["suggestedMapping"] = simplify(event["suggestedMapping"])


def prune(patterns):
    result = []
    for pattern in realize(patterns):
        events = []
        trackVolume = 1.0
        waveform = None
        for event in pattern.to_json()["events"]:
            if event["type"] == "note":
                events.append({
                    "type": "n",
                    "t": event["realTime"],
                    "d": event["realGateLength"],
                    "v": float(Fraction(event["velocity"])),
                    "f": event["realFrequency"],
                    "p": event["phase"],
                })
            if event["type"] == "percussion":
                events.append({
                    "type": "p",
                    "t": event["realTime"],
                    "d": event["realGateLength"],
                    "v": float(Fraction(event["velocity"])),
                    "i": event["index"],
                })
            if event["type"] == "trackVolume":
                trackVolume = float(Fraction(event["volume"]));
            if event["type"] == "waveform":
                waveform = event["name"]
            if event["type"] == "envelope":
                events.append({
                    "type": "envelope",
                    "t": event["realTime"],
                    "attack": float(Fraction(event["attack"])),
                    "decay": float(Fraction(event["decay"])),
                    "sustain": float(Fraction(event["sustain"])),
                    "release": float(Fraction(event["release"])),
                })
        result.append({
            "events": events,
            "maxPolyphony": getattr(pattern, "max_polyphony", 15),
            "volume": trackVolume,
            "waveform": waveform,
        })
    return result


def _tokenize_fractions_chord(pattern):
    pitches = []
    for note in pattern:
        pitches.append(note.pitch.monzo.vector)
    root_fraction = tokenize_fraction(pattern[0].pitch.monzo.vector, PRIMES)
    chord = tokenize_otonal_utonal(pitches, PRIMES)
    return "{}={}".format(root_fraction, chord)


def _tokenize_fractions_pitch(pitch):
    return "{}".format(tokenize_fraction(pitch.monzo.vector, PRIMES))


def _tokenize_absolute_chord(pattern, inflections):
    pitches = [tokenize_pitch(note.pitch.monzo.vector.astype(int), inflections) for note in pattern]
    return "({})".format(",".join(pitches))


def _tokenize_absolute_pitch(pitch, inflections):
    return tokenize_pitch(pitch.monzo.vector.astype(int), inflections)


def tokenize_pattern(pattern, _tokenize_chord, _tokenize_pitch, main=False, absolute_time=False):
    if isinstance(pattern, Spacer):
        return pattern.value
    if isinstance(pattern, ProgramChange):
        return "I:{}".format(pattern.name)
    if isinstance(pattern, ContextChange):
        return "N:{}".format(pattern.name)
    if isinstance(pattern, TrackVolume):
        return "V:{}".format(pattern.volume)
    if isinstance(pattern, UserMessage):
        return pattern.escape()
    if isinstance(pattern, Articulation):
        for symbol, value in ARTICULATIONS.items():
            if value == pattern.gate_ratio:
                return symbol
        return "'{}".format(pattern.gate_ratio)
    if isinstance(pattern, Dynamic):
        for symbol, value in DYNAMICS.items():
            if value == pattern.velocity:
                return symbol
        return "f{}".format(pattern.velocity)
    if pattern.duration == 0:
        return ""
    suffix = ""
    if not main:
        if pattern.duration != 1:
            if absolute_time:
                suffix = "[{} @{}]".format(pattern.duration, pattern.time)
            else:
                suffix = "[{}]".format(pattern.duration)
        elif absolute_time:
            suffix = "[@{}]".format(pattern.time)
    if isinstance(pattern, Pattern):
        pattern.simplify()
        if pattern.is_chord():
            try:
                return _tokenize_chord(pattern) + suffix
            except ValueError:
                pass
        subnotations = []
        previous_time = None
        local_time = Fraction(0)
        for subpattern in pattern:
            force_tokenize = False
            if isinstance(subpattern, (ProgramChange, ContextChange, TrackVolume, Spacer, UserMessage)):
                force_tokenize = True
            if isinstance(subpattern, Articulation):
                force_tokenize = True
                if main and subpattern.time == 0 and subpattern.gate_ratio == ARTICULATIONS[";"]:
                    force_tokenize = False
            if isinstance(subpattern, Dynamic):
                force_tokenize = True
                if main and subpattern.time == 0 and subpattern.velocity == DYNAMICS["mf"]:
                    force_tokenize = False
            if force_tokenize:
                subnotations.append(tokenize_pattern(subpattern, _tokenize_chord, _tokenize_pitch))
            if subpattern.duration == 0:
                continue
            local_absolute_time = False
            if subpattern.time != local_time:
                if subpattern.time == previous_time:
                    subnotations.append(",")
                else:
                    local_absolute_time = True
                local_time = subpattern.time
            subnotations.append(tokenize_pattern(subpattern, _tokenize_chord, _tokenize_pitch, absolute_time=local_absolute_time))
            previous_time = local_time
            local_time += subpattern.duration
        if main:
            return " ".join(filter(None, subnotations))
        return "(" + " ".join(filter(None, subnotations)) + ")" + suffix
    if isinstance(pattern, Note):
        return _tokenize_pitch(pattern.pitch) + suffix
    if isinstance(pattern, Rest):
        return ".{}".format(suffix)
    if isinstance(pattern, Percussion):
        for short, (index, name) in PERCUSSION_SHORTHANDS.items():
            if index == pattern.index:
                return "{}{}".format(short, suffix)

    return ""


def patterns_to_fractions(patterns, outfile):
    for pattern in patterns:
        if pattern.duration <= 0:
            continue
        outfile.write("---\n")
        outfile.write(tokenize_pattern(pattern, _tokenize_fractions_chord, _tokenize_fractions_pitch, True))
        outfile.write("\n")


FREQ_A4 = 440
INDEX_A4 = 69
MIDI_STEP = 2**(1/12)

def freq_to_midi_12(frequency, pitch_bend_depth=2):
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


FREQ_C3 = FREQ_A4 / MIDI_STEP**21
INDEX_C3 = INDEX_A4 - 21

def freq_to_midi_et(frequency, et_divisions, et_divided=2):
    ratio = frequency / FREQ_C3
    steps = log(ratio) / log(float(et_divided)) * float(et_divisions)
    steps += INDEX_C3
    index = int(round(steps))
    bend = steps - index
    if bend < 0:
        bend = int(round(8192*bend*2))
    else:
        bend = int(round(8191*bend*2))
    return index, bend


def midi_velocity(velocity):
    return int(round(float(127 * Fraction(velocity))))


def tracks_to_midi(tracks, freq_to_midi=freq_to_midi_12, reserve_channel_10=True, transpose=0, resolution=960):
    """
    Save tracks as a midi file with per-channel pitch-bend for microtones.

    Assumes that A4 is in standard tuning 440Hz.
    """
    midi = mido.MidiFile()
    channel_offset = 0
    for pattern in realize(tracks):
        max_polyphony = getattr(pattern, "max_polyphony", 15)
        if pattern.duration <= 0:
            continue
        track = mido.MidiTrack()
        midi.tracks.append(track)

        data = pattern.to_json()
        events = []
        time_offset = 0
        for event in data["events"]:
            if event["type"] in ("note", "percussion", "programChange", "contextChange") or event.get("subtype") == "controlChange":
                time = int(round(resolution * event["realTime"]))
            if event["type"] == "note":
                events.append((time, event, event["realFrequency"], midi_velocity(event["velocity"])))
            if event["type"] == "percussion":
                events.append((time, event, None, midi_velocity(event["velocity"])))
            if event["type"] == "programChange" or event.get("subtype") == "controlChange":
                change_time = time - 1
                if change_time < 0:
                    time_offset = -change_time
                events.append((change_time, event, None, None))
            if event["type"] == "contextChange":
                events.append((time - 1.1, event, None, None))
        presorted = events
        events = []
        channel = channel_offset
        key = lambda t: (t[0], t[2], t[3])
        for time, event, frequency, velocity in sorted(presorted, key=key):
            if event["type"] in ("note", "percussion"):
                duration = int(round(resolution * event["realGateLength"]))
                if duration <= 0:
                    continue
                max_duration = int(resolution * event["realDuration"])
                if duration >= max_duration:
                    duration = max_duration - 1
            if event["type"] == "note":
                index, bend = freq_to_midi(frequency)
                index += transpose
                channel_ = channel
                if reserve_channel_10 and channel >= 9:
                    channel_ += 1
                events.append((time, "note_on", index, bend, velocity, channel_))
                events.append((time + duration, "note_off", index, bend, velocity, channel_))
                channel = ((channel - channel_offset + 1) % max_polyphony) + channel_offset
            if event["type"] == "percussion":
                index = event["index"]
                if reserve_channel_10:
                    channel_ = 9
                else:
                    channel_ = channel
                    channel = ((channel - channel_offset + 1) % max_polyphony) + channel_offset
                events.append((time, "note_on", index, None, velocity, channel_))
                events.append((time + duration, "note_off", index, None, velocity, channel_))
            if event["type"] == "programChange":
                events.append((time, "program_change", event["program"], None, None, None))
            if event.get("subtype") == "controlChange":
                events.append((time, "control_change", event["control"], None, event["value"], None))
            if event["type"] == "contextChange":
                events.append((time, "_context_change", event["name"], None, None, None))

        default_range = []
        for ch in range(max_polyphony):
            ch += channel_offset
            if reserve_channel_10 and ch >= 9:
                ch += 1
            default_range.append(ch)
        percussion_range = default_range
        if reserve_channel_10:
            percussion_range = [9]
        channel_ranges = {"percussion": percussion_range}

        current_context = "hewmp"
        current_time = 0
        for event in sorted(events):
            time, msg_type, index, bend, velocity, channel = event
            time += time_offset
            if msg_type == "_context_change":
                current_context = index
            elif msg_type == "program_change":
                for ch in channel_ranges.get(current_context, default_range):
                    message = mido.Message(msg_type, program=index, channel=ch, time=(time - current_time))
                    track.append(message)
                    current_time = time
            elif msg_type == "control_change":
                for ch in channel_ranges.get(current_context, default_range):
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
        target_time = int(round(resolution * data["realDuration"]))
        message = mido.MetaMessage("end_of_track", time=max(0, target_time - current_time))
        track.append(message)

        channel_offset += max_polyphony

    return midi


if __name__ == "__main__":
    import argparse
    import sys
    import json
    import os.path

    parser = argparse.ArgumentParser(description='Parse input file (or stdin) in HEWMP notation and output JSON to file (or stdout)')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('--simplify', action='store_true')
    parser.add_argument('--fractional', action='store_true')
    parser.add_argument('--absolute', action='store_true')
    parser.add_argument('--midi', action='store_true')
    parser.add_argument('--midi-et', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--pitch-bend-depth', type=int, default=2)
    parser.add_argument('--override-channel-10', action='store_true')
    parser.add_argument('--midi-transpose', type=int, default=0)
    parser.add_argument('--track', type=int)
    args = parser.parse_args()

    patterns, config = parse_file(args.infile)
    if args.track is not None:
        tracks = patterns
        patterns = []
        for index, track in enumerate(tracks):
            if index == 0 or index == args.track:
                patterns.append(track)
    if args.infile is not sys.stdin:
        args.infile.close()

    file_extension = os.path.splitext(args.outfile.name)[-1].lower()
    export_midi = (args.midi or args.midi_et or file_extension == ".mid")
    if args.json:
        export_midi = False

    if args.fractional:
        patterns_to_fractions(patterns, args.outfile)
    elif args.absolute:
        inflections = reverse_inflections(DEFAULT_INFLECTIONS)
        _chord = lambda pattern: _tokenize_absolute_chord(pattern, inflections)
        _pitch = lambda pattern: _tokenize_absolute_pitch(pattern, inflections)
        for pattern in patterns:
            if pattern.duration <= 0:
                continue
            pattern.transpose(config["interval_parser"].base_pitch)
            if "comma_reduction_cache" in config:
                comma_reduce_pattern(pattern, config["tuning"].comma_list, config["CRD"], config["comma_reduction_cache"])
            args.outfile.write("---\n")
            args.outfile.write(tokenize_pattern(pattern, _chord, _pitch, True))
            args.outfile.write("\n")
    elif export_midi:
        if mido is None:
            raise ValueError("Missing mido package")
        if args.outfile is sys.stdout:
            outfile = args.outfile
        else:
            filename = args.outfile.name
            args.outfile.close()
            outfile = open(filename, "wb")
        if args.midi_et:
            et_divisions = config["tuning"].et_divisions
            et_divided = config["tuning"].et_divided
            freq_to_midi = lambda freq: freq_to_midi_et(freq, et_divisions, et_divided)
        else:
            freq_to_midi = lambda freq: freq_to_midi_12(freq, args.pitch_bend_depth)
        midi = tracks_to_midi(patterns, freq_to_midi, not args.override_channel_10, args.midi_transpose)
        midi.save(file=outfile)
    else:
        result = {
            "tracks": [],
        }
        for pattern in realize(patterns):
            result["tracks"].append(pattern.to_json())
        if args.simplify:
            simplify_tracks(result)
        json.dump(result, args.outfile)

    if args.outfile is not sys.stdout:
        args.outfile.close()
    elif not args.fractional and not args.absolute:
        args.outfile.write("\n")
