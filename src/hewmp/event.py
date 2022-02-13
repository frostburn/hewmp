from math import gcd
from collections import deque
from fractions import Fraction
from numpy import array, zeros, log, floor, pi, around, dot, exp, cumsum, linspace, concatenate, ones
from scipy.interpolate import interp1d
from .temperament import temper_subgroup, comma_reduce, comma_equals, comma_root
from .notation import tokenize_fraction
from .monzo import PRIMES, Mapping


DEFAULT_METRIC = ones(len(PRIMES))
DEFAULT_METRIC[0] = 4  # Optimize error for 16 not 2
DEFAULT_METRIC[1] = 2  # Optimize error for 9 not 3


class MusicBase:
    def __init__(self, time, duration, real_time=None, real_duration=None):
        self.time = Fraction(time)
        self.duration = Fraction(duration)
        self.real_time = real_time
        self.real_duration = real_duration

    @property
    def end_time(self):
        return self.time + self.duration

    @end_time.setter
    def end_time(self, value):
        self.duration = value - self.time


    @property
    def real_end_time(self):
        return self.real_time + self.real_duration

    @real_end_time.setter
    def real_end_time(self, value):
        self.real_duration = value - self.real_time

    def to_json(self):
        return {
            "time": str(self.time),
            "duration": str(self.duration),
            "realTime": None if self.real_time is None else float(self.real_time),
            "realDuration": None if self.real_time is None else float(self.real_duration),
        }

    def retime(self, time, duration):
        raise ValueError("Sub-classes must implement retiming")

    def copy(self):
        return self.retime(self.time, self.duration)

    def extend_duration(self, extension):
        self.duration += extension


class Event(MusicBase):
    def flatten(self):
        return [self]


class Tuning(Event):
    def __init__(self, base_frequency, comma_list, constraints, subgroup, et_divisions=None, et_divided=None, warts=None, suggested_mapping=None, time=0, duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
        self.base_frequency = base_frequency
        self.comma_list = comma_list
        self.constraints = constraints
        self.subgroup = subgroup
        self.et_divisions = et_divisions
        self.et_divided = et_divided
        self.warts = warts
        self.suggested_mapping = suggested_mapping
        self.cache = {}

    def suggest_mapping(self):
        JI = log(array(PRIMES))
        if self.et_divisions is None or self.et_divided is None or self.warts is None:
            mapping = temper_subgroup(
                JI,
                [comma[:len(JI)] for comma in self.comma_list],
                [constraint[:len(JI)] for constraint in self.constraints],
                [basis_vector[:len(JI)] for basis_vector in self.subgroup],
                metric=DEFAULT_METRIC,
            )
        else:
            generator = log(float(self.et_divided)) / float(self.et_divisions)
            if generator == 0:
                mapping = JI*0
            else:
                steps = around(JI/generator)
                mapping = steps*generator
                for index, count in enumerate(self.warts):
                    modification = ((count + 1)//2) * (2*(count%2) - 1)
                    if mapping[index] > JI[index]:
                        steps[index] -= modification
                    else:
                        steps[index] += modification
                mapping = steps*generator
        self.suggested_mapping = Mapping(mapping, self.base_frequency)

    def to_json(self):
        result = super().to_json()
        comma_list = ",".join(tokenize_fraction(comma, PRIMES) for comma in self.comma_list)
        constraints = ",".join(tokenize_fraction(constraint, PRIMES) for constraint in self.constraints)
        subgroup = ".".join(tokenize_fraction(basis_vector, PRIMES) for basis_vector in self.subgroup)
        result.update({
            "type": "tuning",
            "baseFrequency": self.base_frequency,
            "commaList": comma_list,
            "constraints": constraints,
            "subgroup": subgroup,
            "equalTemperament": [None if self.et_divisions is None else str(self.et_divisions), None if self.et_divided is None else str(self.et_divided)],
            "warts": None if self.warts is None else list(self.warts),
            "suggestedMapping": list(self.suggested_mapping.vector),
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
            self.et_divisions,
            self.et_divided,
            warts,
            self.suggested_mapping,
            time,
            duration
        )

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.__class__.__name__,
            self.base_frequency,
            self.comma_list,
            self.constraints,
            self.subgroup,
            self.et_divisions,
            self.et_divided,
            self.warts,
            self.suggested_mapping,
            self.time,
            self.duration,
            self.real_time,
            self.real_duration,
        )

    def equals(self, pitch_a, pitch_b, persistence=5):
        """
        Check if two pitches are comma-equal
        """
        return comma_equals(pitch_a, pitch_b, self.comma_list, persistence=persistence, cache=self.cache)


class Tempo(Event):
    def __init__(self, tempo_unit, tempo_duration, beat_unit, groove_pattern=None, groove_span=None, time=0, duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
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
            "groovePattern": None if self.groove_pattern is None else list(map(str, self.groove_pattern)),
            "grooveSpan": None if self.groove_span is None else str(self.groove_span),
        })
        return result

    def retime(self, time, duration):
        return self.__class__(self.tempo_unit, self.tempo_duration, self.beat_unit, self.groove_pattern, self.groove_span, time, duration)

    def to_real_time(self, time, duration):
        start_beat = float(time)
        end_beat = float(time + duration)
        beat_duration = float(self.beat_duration)
        if self.groove_span is None:
            return start_beat*beat_duration, (end_beat - start_beat)*beat_duration

        unit = float(self.groove_span/self.beat_unit)

        groove_bars, groove_beat = divmod(start_beat, unit)
        start_time = (groove_bars + self.groove(groove_beat/unit)) * unit

        groove_bars, groove_beat = divmod(end_beat, unit)
        end_time = (groove_bars + self.groove(groove_beat/unit)) * unit

        return start_time*beat_duration, (end_time - start_time)*beat_duration

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.__class__.__name__,
            self.tempo_unit,
            self.tempo_duration,
            self.beat_unit,
            self.groove_pattern,
            self.groove_span,
            self.time,
            self.duration,
            self.real_time,
            self.real_duration,
        )


class Rest(Event):
    def __init__(self, time=0, duration=1, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "rest"
        return result

    def retime(self, time, duration):
        return self.__class__(time, duration)


class Spacer(Event):
    def __init__(self, value, time=0, duration=0, real_time=None, real_duration=None):
        if real_time is not None or real_duration is not None:
            raise ValueError("Spacers shouldn't be realized")
        super().__init__(time, duration, real_time=None, real_duration=None)
        self.value = value

    def to_json(self):
        raise ValueError("Spacers cannot be converted to json")

    def retime(self, time, duration):
        return self.__class__(self.value, time, duration)


class NewLine(Spacer):
    pass


class BarLine(Spacer):
    pass


class Playhead(Spacer):
    pass


class Playstop(Spacer):
    pass


class Dynamic(Event):
    def __init__(self, velocity, time=0, duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
        self.velocity = velocity

    def retime(self, time, duration):
        return self.__class__(self.velocity, time ,duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "dynamic"
        result["velocity"] = str(self.velocity)
        return result


class Articulation(Event):
    def __init__(self, gate_ratio, time=0, duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
        self.gate_ratio = gate_ratio

    def retime(self, time, duration):
        return self.__class__(self.gate_ratio, time ,duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "articulation"
        result["gateRatio"] = str(self.gate_ratio)
        return result


class ContextChange(Event):
    def __init__(self, name, time=0, duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
        self.name = name

    def retime(self, time, duration):
        return self.__class__(self.name, time, duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "contextChange"
        result["name"] = self.name
        return result


class ControlChange(Event):
    def __init__(self, control, value, time=0, duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
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
    def __init__(self, volume, time=0, duration=0, real_time=None, real_duration=None):
        super().__init__(7, None, time, duration, real_time, real_duration)
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
    def __init__(self, message, time, duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
        self.message = message

    def retime(self, time, duration):
        return self.__class__(self.message, time, duration)

    def to_json(self):
        result = super().to_json()
        result["type"] = "userMessage"
        result["message"] = self.message
        return result

    def escape(self):
        return '"{}"'.format(self.message.replace("$", "$$").replace('"', '$"'))


class ProgramChange(Event):
    def __init__(self, name, program, time, duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
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
    def transpose(self, interval):
        raise ValueError("Sub-classes should implement transposing")


class GatedEvent(Event):
    def __init__(self, time=0, duration=1, real_time=None, real_duration=None, real_gate_length=None):
        super().__init__(time, duration, real_time, real_duration)
        self.real_gate_length = real_gate_length

    def to_json(self):
        result = super().to_json()
        result["realGateLength"] = self.real_gate_length
        return result


class Note(GatedEvent, Transposable):
    def __init__(self, pitch, velocity=None, gate_ratio=None, time=0, duration=1, real_time=None, real_duration=None, real_gate_length=None, real_frequency=None):
        super().__init__(time, duration, real_time, real_duration, real_gate_length)
        self.pitch = pitch
        self.velocity = velocity
        self.gate_ratio = gate_ratio
        self.real_frequency = real_frequency

    def transpose(self, interval):
        self.pitch = self.pitch + interval

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.__class__.__name__, self.pitch, self.velocity, self.gate_ratio,
            self.time, self.duration, self.real_time, self.real_duration, self.real_gate_length, self.real_frequency
        )

    def to_json(self):
        result = super().to_json()
        result.update({
            "type": "note",
            "monzo": [float(component) for component in self.pitch.monzo.vector],
            "centOffset": self.pitch.monzo.nats / log(2) * 1200,
            "frequencyOffset": self.pitch.frequency_offset,
            "phase": self.pitch.phase * 360 / (2*pi),
            "velocity": str(self.velocity),
            "gate_ratio": str(self.gate_ratio),
            "realFrequency": self.real_frequency,
        })
        return result

    def retime(self, time, duration):
        return self.__class__(self.pitch.copy(), self.velocity, self.gate_ratio, time, duration, real_gate_length=self.real_gate_length, real_frequency=self.real_frequency)


class Percussion(GatedEvent):
    def __init__(self, name, index=None, velocity=None, gate_ratio=None, time=0, duration=1, real_time=None, real_duration=None, real_gate_length=None):
        super().__init__(time, duration, real_time, real_duration, real_gate_length)
        self.name = name
        self.index = index
        self.velocity = velocity
        self.gate_ratio = gate_ratio

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.__class__.__name__, self.name, self.index, self.velocity, self.gate_ratio,
            self.time, self.duration, self.real_time, self.real_duration, self.real_gate_length
        )

    def to_json(self):
        result = super().to_json()
        result.update({
            "type": "percussion",
            "name": self.name,
            "index": self.index,
            "velocity": self.velocity,
            "gate_ratio": self.gate_ratio,
        })
        return result

    def retime(self, time, duration):
        return self.__class__(self.name, self.index, self.velocity, self.gate_ratio, time, duration, real_gate_length=self.real_gate_length)


class Pattern(MusicBase, Transposable):
    def __init__(self, subpatterns=None, time=0, duration=1, logical_duration=0, real_time=None, real_duration=None):
        super().__init__(time, duration, real_time, real_duration)
        if subpatterns is None:
            self.subpatterns = []
        else:
            self.subpatterns = subpatterns
        self.logical_duration = logical_duration

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

    def __setitem__(self, index, value):
        self.subpatterns[index] = value

    def __len__(self):
        return len(self.subpatterns)

    def __iter__(self):
        return iter(self.subpatterns)

    @property
    def t(self):
        return self.logical_duration

    @t.setter
    def t(self, value):
        self.logical_duration = value

    @property
    def last(self):
        for event in reversed(self.subpatterns):
            if not isinstance(event, Spacer):
                return event
        raise IndexError("No last event found")

    @last.setter
    def last(self, value):
        for i in range(len(self)):
            i += 1
            if not isinstance(self[-i], Spacer):
                self[-i] = value
                return

    @property
    def last_voiced(self):
        for event in reversed(self.subpatterns):
            if isinstance(event, (Note, Percussion, Pattern)):
                return event

    def simplify(self):
        common_denominator = 0
        for subpattern in self.subpatterns:
            if not isinstance(subpattern.duration, Fraction) or not isinstance(subpattern.time, Fraction):
                return
            common_denominator = gcd(subpattern.duration.denominator, common_denominator)
            if subpattern.time != 0:
                common_denominator = gcd(subpattern.time.denominator, common_denominator)
        for subpattern in self.subpatterns:
            subpattern.time *= common_denominator
            subpattern.duration *= common_denominator

        common_divisor = 0
        for subpattern in self.subpatterns:
            common_divisor = gcd(subpattern.duration.numerator, common_divisor)
            common_divisor = gcd(subpattern.time.numerator, common_divisor)
        for subpattern in self.subpatterns:
            subpattern.time /= common_divisor
            subpattern.duration /= common_divisor


    def repeat(self, num_repeats, affect_duration=False):
        subpatterns = self.subpatterns
        self.subpatterns = []
        offset = 0
        for _ in range(num_repeats):
            self.subpatterns += [sub.retime(sub.time + offset, sub.duration) for sub in subpatterns]
            offset += self.logical_duration
        self.logical_duration *= num_repeats
        if affect_duration:
            self.duration *= num_repeats

    def fill(self, num_onsets):
        subpatterns = self.subpatterns
        self.subpatterns = []
        offset = 0
        while len(self) < num_onsets:
            for subpattern in subpatterns:
                self.subpatterns.append(subpattern.retime(subpattern.time + offset, subpattern.duration))
                if len(self) >= num_onsets:
                    break
            offset += self.logical_duration
        self.logical_duration = self.last.end_time

    def reverse_time(self):
        for subpattern in self.subpatterns:
            start_time = subpattern.time
            end_time = subpattern.end_time
            subpattern.time = self.logical_duration - end_time
            subpattern.end_time = self.logical_duration - start_time

    def reverse_logic(self):
        self.subpatterns = self.subpatterns[::-1]

    def _rotate_time(self, steps):
        offset = self[steps % len(self)].time
        for subpattern in self:
            subpattern.time = (subpattern.time - offset) % self.logical_duration

    def _rotate_logic(self, steps):
        times_durations = [(sub.time, sub.duration) for sub in self]
        for i in range(len(self)):
            self.subpatterns[i].time, self.subpatterns[i].duration = times_durations[(i+steps)%len(self)]

    def rotate_rhythm(self, steps):
        self._rotate_time(steps)
        self._rotate_logic(steps)

    def rotate_time(self, steps):
        self._rotate_time(steps)
        d = deque(self.subpatterns)
        d.rotate(-steps)
        self.subpatterns = list(d)

    def stretch_subpatterns(self):
        for subpattern in self:
            subpattern.end_time = self.logical_duration

    def extend_duration(self, extension):
        logical_extension = extension * self.logical_duration / self.duration
        for subpattern in self.subpatterns:
            subpattern.extend_duration(logical_extension)
        self.logical_duration += logical_extension
        super().extend_duration(extension)

    def concatenate(self, other, add_durations):
        duration = self.duration
        if add_durations:
            duration += other.duration
        result = Pattern([], self.time, duration, self.logical_duration + other.logical_duration)
        for subpattern in self.subpatterns:
            result.append(subpattern.copy())
        offset = self.logical_duration
        for subpattern in other.subpatterns:
            result.append(subpattern.retime(subpattern.time + offset, subpattern.duration))
        return result

    def flatten(self):
        if self.logical_duration == 0:
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

    def transpose(self, interval):
        for subpattern in self.subpatterns:
            if isinstance(subpattern, Transposable):
                subpattern.transpose(interval)

    def realize(self, start_time=None, end_time=None):
        flat = []
        tempo = None
        tuning = None
        articulation = None
        dynamic = None
        for event in self.flatten():
            if not isinstance(event, Spacer):
                flat.append(event)
            if isinstance(event, Tempo) and tempo is None:
                tempo = event
            if isinstance(event, Tuning):
                if tuning is None:
                    tuning = event
            if isinstance(event, Articulation) and articulation is None:
                articulation = event
            if isinstance(event, Dynamic) and dynamic is None:
                dynamic = event
        events = []

        missing = {
            Articulation: None,
            Dynamic: None,
            ProgramChange: None,
            TrackVolume: None,
            ContextChange: None,
        }
        if start_time is not None:
            start_real_time, _ = tempo.to_real_time(start_time, 0)
        else:
            start_real_time = 0.0
        for event in flat:
            if isinstance(event, Articulation):
                articulation = event
            if isinstance(event, Dynamic):
                dynamic = event
            real_time, real_duration = tempo.to_real_time(event.time, event.duration)
            if isinstance(event, GatedEvent):
                event.gate_ratio = articulation.gate_ratio
                event.velocity = dynamic.velocity
                _, real_gate_length = tempo.to_real_time(event.time, event.duration * articulation.gate_ratio)
                if real_gate_length <= 0:
                    continue
                event.real_gate_length = real_gate_length
            if isinstance(event, Note):
                event.real_frequency = tuning.suggested_mapping(event.pitch)
            if start_time is not None and event.time < start_time:
                for type_ in missing:
                    if isinstance(event, type_):
                        missing[type_] = event
                continue
            if end_time is not None and event.end_time > end_time:
                continue
            if start_time is not None:
                event = event.retime(event.time - start_time, event.duration)
            real_time -= start_real_time
            for type_, missing_event in list(missing.items()):
                if missing_event is not None:
                    extra = missing_event.retime(event.time, 0)
                    extra.real_time = real_time
                    extra.real_duration = 0.0
                    events.append(extra)
                    missing[type_] = None
            event.real_time = real_time
            event.real_duration = real_duration
            events.append(event)

        if start_time is None:
            start_time = self.time
        if end_time is None:
            end_time = self.end_time
        for thing in [tempo, tuning]:
            if start_time > thing.time:
                extra = thing.copy()
                extra.real_time = 0.0
                extra.real_duration = 0.0
                events.insert(0, extra)
        duration = end_time - start_time
        real_time, real_duration = tempo.to_real_time(start_time, duration)
        return Pattern(events, start_time, duration, duration, real_time, real_duration)

    def retime(self, time, duration):
        result = self.__class__([], time, duration, self.logical_duration)
        for subpattern in self.subpatterns:
            result.append(subpattern.copy())
        return result

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(self.__class__.__name__, self.subpatterns, self.time, self.duration, self.logical_duration, self.real_time, self.real_duration)

    def is_chord(self):
        for note in self:
            if not isinstance(note, Note):
                return False
            if note.time != 0 or note.duration != 1:
                return False
        return True

    @property
    def events(self):
        return self.subpatterns

    def to_json(self):
        return {
            "time": str(self.time),
            "duration": str(self.duration),
            "realTime": self.real_time,
            "realDuration": self.real_duration,
            "events": [event.to_json() for event in self.events]
        }
