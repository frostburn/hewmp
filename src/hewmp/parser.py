# coding: utf-8
from io import StringIO
from collections import Counter
try:
    import mido
except ImportError:
    mido = None
from fractions import Fraction
from .lexer import Lexer, CONFIGS, TRACK_START
from .chord_parser import expand_chord, separate_by_arrows
from .temperaments import TEMPERAMENTS, EQUAL_TEMPERAMENTS
from .notation import tokenize_fraction, tokenize_otonal_utonal, tokenize_pitch, reverse_inflections
from .percussion import PERCUSSION_SHORTHANDS
from .gm_programs import GM_PROGRAMS
from .smitonic import SMITONIC_INTERVAL_QUALITIES, SMITONIC_BASIC_PITCHES, smitonic_parse_arrows, smitonic_parse_pitch, SMITONIC_INFLECTIONS
from .rhythm import sequence_to_time_duration, euclidean_rhythm, mos_rhythm, exponential_rhythm
from .event import *
from .color import parse_interval as parse_color_interval, UNICODE_EXPONENTS


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
    "a4": (-9, 6),
    "a1": (-11, 7),
    "a5": (-12, 8),
    "a2": (-14, 9),
    "a6": (-15, 10),
    "a3": (-17, 11),
    "a7": (-18, 12),

    # Extra neutral intervals
    "N2": (2.5, -1.5),
    "N6": (1.5, -0.5),
    "N3": (-0.5, 0.5),
    "N7": (-1.5, 1.5),

    # Bonus non-standard intervals
    "m4": (7.5, -4.5),
    "m1": (5.5, -3.5),
    "m5": (4.5, -2.5),
    "M4": (-3.5, 2.5),
    "M1": (-5.5, 3.5),
    "M5": (-6.5, 4.5),
}


AUGMENTED_INFLECTION = (-11, 7)
INTERVAL_QUALITIES = "dmPNMa"


def parse_arrows(token, inflections):
    quality = token[0]
    token = token[1:]
    augmented = 0
    while token[0] == "a":
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


class IntervalParser:
    def __init__(self, inflections=DEFAULT_INFLECTIONS, smitonic_inflections=SMITONIC_INFLECTIONS, edn_divisions=Fraction(12), edn_divided=Fraction(2)):
        self.inflections = inflections
        self.smitonic_inflections = smitonic_inflections
        self.edn_divisions = edn_divisions
        self.edn_divided = edn_divided
        self.base_pitch = zero_pitch()
        self.smitonic_base_pitch = zero_pitch()
        self.comma_list = None
        self.comma_root_cache = None
        self.persistence = 5

    def set_base_pitch(self, token):
        if token[0] in BASIC_PITCHES:
            self.base_pitch = parse_pitch(token, self.inflections)
        elif token[0] in SMITONIC_BASIC_PITCHES:
            self.smitonic_base_pitch = smitonic_parse_pitch(token, self.smitonic_inflections)
        else:
            raise ParsingError("Unrecognized absolute pitch {}".format(token))

    def parse(self, token, return_root_degree=False):
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

        if token[0].isdigit() and not is_colored:
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
                divisions = self.edn_divisions
                divided = self.edn_divided
                step_spec = token.split("\\")
                steps = Fraction(step_spec[0])
                if len(step_spec) >= 2 and step_spec[1]:
                    divisions = Fraction(step_spec[1])
                if len(step_spec) == 3:
                    divided = Fraction(step_spec[2])
                pitch[E_INDEX] = float(steps) / float(divisions) * log(float(divided))
            else:
                pitch += parse_fraction(token)
        elif token[0] in INTERVAL_QUALITIES:
            pitch += parse_arrows(token, self.inflections)
        elif token[0] in BASIC_PITCHES:
            if direction is not None:
                raise ParsingError("Signed absolute pitch")
            pitch += parse_pitch(token, self.inflections) - self.base_pitch
            absolute = True
        elif token[0] == "p" or (token[0] in SMITONIC_INTERVAL_QUALITIES and not is_colored):
            pitch += smitonic_parse_arrows(token, self.smitonic_inflections)
        elif token[0] in SMITONIC_BASIC_PITCHES:
            if direction is not None:
                raise ParsingError("Signed absolute pitch")
            pitch += smitonic_parse_pitch(token, self.smitonic_inflections) - self.smitonic_base_pitch
            absolute = True
        else:
            color_monzo = parse_color_interval(token)
            color_offset = zero_pitch()
            color_offset[:len(color_monzo)] = color_monzo
            pitch += color_offset

        if direction is not None:
            pitch *= direction

        if self.comma_list is not None and self.comma_root_cache is not None:
            maybe_pitch = comma_root(pitch * exponent_degree, root_degree, self.comma_list, persistence=self.persistence, cache=self.comma_root_cache)
            if maybe_pitch is not None:
                if return_root_degree:
                    raise ValueError("Cannot return root degree when solving for comma roots")
                return maybe_pitch, absolute
        if return_root_degree:
            return pitch, absolute, exponent_degree, root_degree
        return pitch / root_degree * exponent_degree, absolute


def parse_otonal(token, interval_parser):
    subtokens = token.split(":")
    pitches = []
    for subtoken in subtokens:
        pitch, absolute = interval_parser.parse(subtoken)
        if absolute:
            raise ParsingError("Otonal chord using absolute pitches")
        pitches.append(pitch)
    root = pitches[0]
    for i in range(len(pitches)):
        pitches[i] = pitches[i] - root
    return Pattern([Note(pitch) for pitch in pitches])


def parse_utonal(token, interval_parser):
    subtokens = token.split(";")
    pitches = []
    for subtoken in subtokens:
        pitch, absolute = interval_parser.parse(subtoken)
        if absolute:
            raise ParsingError("Utonal chord using absolute pitches")
        pitches.append(pitch)
    root = pitches[0]
    for i in range(len(pitches)):
        pitches[i] = root - pitches[i]
    return Pattern([Note(pitch) for pitch in pitches])


def parse_chord(token, transposition, interval_parser):
    inversion = 0
    if "_" in token:
        token, inversion_token = token.split("_")
        inversion = int(inversion_token)
    if ":" in token:
        result = parse_otonal(token, interval_parser)
        result.transpose(transposition)
    elif ";" in token:
        result = parse_utonal(token, interval_parser)
        result.transpose(transposition)
    else:
        subtokens = expand_chord(token)
        result = Pattern()
        for subtoken in subtokens:
            pitch, absolute = interval_parser.parse(subtoken)
            if absolute:
                result.append(Note(pitch))
            else:
                result.append(Note(pitch + transposition))
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


def patternify(pattern):
    if not isinstance(pattern, Pattern):
        pattern = Pattern([pattern], time=pattern.time, duration=pattern.duration)
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
    if "interval_parser" in default_config:
        interval_parser = default_config["interval_parser"]
    else:
        interval_parser = IntervalParser()

    config = {}
    config.update(default_config)
    config["tuning"] = config["tuning"].copy()
    config["tempo"] = config["tempo"].copy()
    config["flags"] = list(config["flags"])
    current_notation = config["N"]
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
                    interval_parser.set_base_pitch(subtoken.strip())
            if config_key == "T":
                tuning_name = token.strip()
                if tuning_name in TEMPERAMENTS:
                    comma_list, subgroup = TEMPERAMENTS[tuning_name]
                    subgroup = subgroup.split(".")
                    config["tuning"].subgroup = [interval_parser.parse(basis_vector)[0] for basis_vector in subgroup]
                    config["tuning"].comma_list = [interval_parser.parse(comma)[0] for comma in comma_list]
                elif tuning_name in EQUAL_TEMPERAMENTS:
                    edn_divisions, edn_divided = EQUAL_TEMPERAMENTS[tuning_name]
                    config["tuning"].edn_divisions = edn_divisions
                    interval_parser.edn_divisions = edn_divisions
                    config["tuning"].edn_divided = edn_divided
                    interval_parser.edn_divided = edn_divided
                    config["tuning"].warts = [0]*len(PRIMES)
                    if "unmapEDN" in config["flags"]:
                        config["flags"].remove("unmapEDN")
                else:
                    raise ParsingError("Unrecognized tuning '{}'".format(tuning_name))
            if config_key == "CL":
                comma_list = [comma.strip() for comma in token.split(",")]
                config["tuning"].comma_list = [interval_parser.parse(comma)[0] for comma in comma_list]
            if config_key == "SG":
                subgroup = [basis_fraction.strip() for basis_fraction in token.split(".")]
                config["tuning"].subgroup = [interval_parser.parse(basis_vector)[0] for basis_vector in subgroup]
            if config_key == "C":
                constraints = [constraint.strip() for constraint in token.split(",")]
                config["tuning"].constraints = [interval_parser.parse(constraint)[0] for constraint in constraints]
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
                edn_divisions = Fraction(token)
                config["tuning"].edn_divisions = edn_divisions
                interval_parser.edn_divisions = edn_divisions
            if config_key == "EDN":
                edn_divided = Fraction(token)
                config["tuning"].edn_divided = edn_divided
                interval_parser.edn_divided = edn_divided
            if config_key == "N":
                current_notation = token.strip()
                if current_notation not in ["hewmp", "HEWMP", "percussion"]:
                    raise ParsingError("Unknown notation '{}'".format(current_notation))
                current_notation = current_notation.lower()
                config[config_key] = current_notation
                pattern.append(ContextChange(current_notation, time))
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
                if "CR" in config["flags"]:
                    config["comma_reduction_cache"] = {}
                if "CRS" in config["flags"]:
                    interval_parser.comma_list = config["tuning"].comma_list
                    interval_parser.comma_root_cache = {}
            config_mode = False
            continue

        if time_mode:
            default = False
            if token == "]":
                time_mode = False
            elif token == ".":
                time -= pattern.last.duration
                pattern.last.duration = 1
                time += pattern.last.duration
            elif token == "?":
                time -= pattern.last.duration
                pattern.last.duration = pattern.last.logical_duration
                time += pattern.last.duration
            elif token.startswith("+") or token.startswith("-"):
                time -= pattern.last.duration
                extension = parse_time(token)
                if isinstance(pattern.last, Pattern):
                    logical_extension = pattern.last.logical_duration * extension / pattern.last.duration
                    for subpattern in pattern.last:
                        subpattern.end_time += logical_extension
                pattern.last.duration += extension
                time += pattern.last.duration
            elif token.startswith("@"):
                time_token = token[1:]
                if time_token == "T":
                    time = timestamp
                else:
                    time = parse_time(time_token)
                pattern.last.time = time
            elif token.lower().startswith("x"):
                pattern.last = patternify(pattern.last)
                time -= pattern.last.duration
                pattern.last.repeat(int(token[1:]), affect_duration=(token.startswith("X")))
                time += pattern.last.duration
            elif "E" in token:
                pattern.last = patternify(pattern.last)
                onset_token = token[:token.index("E")]
                if onset_token:
                    pattern.last.fill(int(onset_token))
                num_onsets = len(pattern.last)
                num_beats = int(token[token.index("E")+1:])
                times_durations = sequence_to_time_duration(euclidean_rhythm(num_onsets, num_beats))
                for subpattern, td in zip(pattern.last, times_durations):
                    subpattern.time, subpattern.duration = td
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
                elif token == "!":
                    pattern.last.stretch_subpatterns()
                elif "e" in token:
                    num_onsets = len(pattern.last)
                    root_token = token[:token.index("e")]
                    if root_token:
                        root = Fraction(root_token)
                    else:
                        root = Fraction(1)
                    factor = Fraction(token[token.index("e")+1:]) ** (1 / root)
                    times_durations = exponential_rhythm(num_onsets, factor)
                    for subpattern, td in zip(pattern.last, times_durations):
                        subpattern.time, subpattern.duration = td
                elif "MOS" in token:
                    num_onsets = len(pattern.last)
                    generator = Fraction(token[:token.index("M")])  # TODO: search for a balanced generator if missing
                    period_token = token[token.index("S")+1:]
                    if period_token:
                        period = Fraction(period_token)
                    else:
                        period = Fraction(1)
                    times_durations = mos_rhythm(num_onsets, generator, period)
                    for subpattern, td in zip(pattern.last, times_durations):
                        subpattern.time, subpattern.duration = td
                else:
                    default = True
            else:
                default = True
            if default:
                duration_token = token
                time -= pattern.last.duration
                pattern.last.duration *= parse_time(duration_token)
                time += pattern.last.duration
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
            time -= pattern.last.duration
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
        elif token == "\n":
            pattern.append(NewLine(token, time))
        elif token == "|":
            pattern.append(BarLine(token, time))
        elif token == "|>":
            pattern.append(Playhead(token, time))
        elif token == ">|":
            pattern.append(Playstop(token, time))
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
                if token_obj.whitespace or not token.startswith("=") or not pattern or isinstance(pattern[-1], NewLine):
                    subpattern_time = time
                    subpattern_duration = Fraction(1)
                    time += subpattern_duration
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
            else:
                moves_root = False
                if token.startswith("~"):
                    moves_root = True
                    token = token[1:]
                interval, absolute = interval_parser.parse(token)

                if transposed_pattern:
                    if absolute:
                        raise ParsingError("Absolute transposition")
                    transposed_pattern.transpose(interval)
                    pattern.append(transposed_pattern)
                    transposed_pattern = None
                    if moves_root:
                        current_pitch += interval
                else:
                    if absolute:
                        if moves_root:
                            raise ParsingError("Superfluous root move (~) with an absolute pitch")
                        current_pitch = zero_pitch()
                        moves_root = True
                    pitch = current_pitch + interval
                    if moves_root:
                        current_pitch = pitch
                    note = Note(pitch, time)
                    pattern.append(note)
                    time += note.duration
                if "comma_reduction_cache" in config:
                    current_pitch = comma_reduce(current_pitch, config["tuning"].comma_list, persistence=config["CRD"], cache=config["comma_reduction_cache"])

    pattern.insert(0, Articulation(ARTICULATIONS[";"]))
    pattern.insert(0, Dynamic(DYNAMICS["mf"]))

    pattern.insert(0, config["tempo"])

    if "unmapEDN" in config["flags"]:
        config["tuning"].warts = None
    config["tuning"].suggest_mapping()
    pattern.insert(0, config["tuning"])

    pattern.duration = pattern.logical_duration

    if max_polyphony is not None:
        pattern.max_polyphony = max_polyphony

    config["interval_parser"] = interval_parser
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
    return results, global_config


def parse_text(text):
    return parse_file(StringIO(text))


def simplify_tracks(data):
    used = array([False] * len(SEMANTIC))

    for track in data["tracks"]:
        for event in track["events"]:
            if event["type"] == "note":
                for i, coord in enumerate(event["pitch"]):
                    if coord != 0:
                        used[i] = True

    data["semantic"] = list(array(SEMANTIC)[used])

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
                event["pitch"] = simplify(event["pitch"])

            if event["type"] == "tuning":
                event["suggestedMapping"] = simplify(event["suggestedMapping"])


def _tokenize_fractions_chord(pattern):
    pitches = []
    for note in pattern:
        pitches.append(note.pitch)
    root_fraction = tokenize_fraction(pattern[0].pitch, PRIMES, E_INDEX, HZ_INDEX, RAD_INDEX)
    chord = tokenize_otonal_utonal(pitches, PRIMES)
    return "{}={}".format(root_fraction, chord)


def _tokenize_fractions_pitch(pitch):
    return "{}".format(tokenize_fraction(pitch, PRIMES, E_INDEX, HZ_INDEX, RAD_INDEX))


def _tokenize_absolute_chord(pattern, inflections):
    pitches = []
    for note in pattern:
        pitches.append(note.pitch)
    pitches = [tokenize_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX) for pitch in pitches]
    return "({})".format(",".join(pitches))


def _tokenize_absolute_pitch(pitch, inflections):
    return tokenize_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)


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
            return _tokenize_chord(pattern) + suffix
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
            if subpattern.duration == 0 and not force_tokenize:
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
        if pattern.emit:
            return "Z{}".format(suffix)
        return "z{}".format(suffix)
    if isinstance(pattern, Percussion):
        for short, (index, name) in PERCUSSION_SHORTHANDS.items():
            if index == pattern.index:
                return "{}{}".format(short, suffix)

    return ""


FREQ_A4 = 440
INDEX_A4 = 69
MIDI_STEP = 2**(1/12)

def freq_to_midi_12(frequency, pitch_bend_depth):
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

def freq_to_midi_edn(frequency, edn_divisions, edn_divided=2):
    ratio = frequency / FREQ_C3
    steps = log(ratio) / log(float(edn_divided)) * float(edn_divisions)
    steps += INDEX_C3
    index = int(round(steps))
    bend = steps - index
    if bend < 0:
        bend = int(round(8192*bend*2))
    else:
        bend = int(round(8191*bend*2))
    return index, bend


def tracks_to_midi(tracks, freq_to_midi, reserve_channel_10=True, transpose=0, resolution=960):
    """
    Save tracks as a midi file with per-channel pitch-bend for microtones.

    Assumes that A4 is in standard tuning 440Hz.
    """
    midi = mido.MidiFile()
    channel_offset = 0
    for pattern, (start_time, end_time) in zip(tracks, sync_playheads(tracks)):
        max_polyphony = getattr(pattern, "max_polyphony", 15)
        if pattern.duration <= 0:
            continue
        track = mido.MidiTrack()
        midi.tracks.append(track)

        data = pattern.realize(start_time=start_time, end_time=end_time).to_json()
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
            if event["type"] in ("note", "percussion", "programChange", "contextChange") or event.get("subtype") == "controlChange":
                time = int(round(resolution * event["realTime"]))
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
    parser.add_argument('--midi-edn', action='store_true')
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
    export_midi = (args.midi or args.midi_edn or file_extension == ".mid")
    if args.json:
        export_midi = False

    if args.fractional:
        for pattern in patterns:
            if pattern.duration <= 0:
                continue
            args.outfile.write("---\n")
            args.outfile.write(tokenize_pattern(pattern, _tokenize_fractions_chord, _tokenize_fractions_pitch, True))
            args.outfile.write("\n")
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
        if args.midi_edn:
            edn_divisions = config["tuning"].edn_divisions
            edn_divided = config["tuning"].edn_divided
            freq_to_midi = lambda freq: freq_to_midi_edn(freq, edn_divisions, edn_divided)
        else:
            freq_to_midi = lambda freq: freq_to_midi_12(freq, args.pitch_bend_depth)
        midi = tracks_to_midi(patterns, freq_to_midi, not args.override_channel_10, args.midi_transpose)
        midi.save(file=outfile)
    else:
        semantic = SEMANTIC
        result = {
            "semantic": SEMANTIC,
            "tracks": [],
        }
        for pattern, (start_time, end_time) in zip(patterns, sync_playheads(patterns)):
            result["tracks"].append(pattern.realize(semantic, start_time, end_time).to_json())
        if args.simplify:
            simplify_tracks(result)
        json.dump(result, args.outfile)

    if args.outfile is not sys.stdout:
        args.outfile.close()
    elif not args.fractional and not args.absolute:
        args.outfile.write("\n")
