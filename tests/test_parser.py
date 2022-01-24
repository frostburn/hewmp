from fractions import Fraction
from numpy import array, dot, isclose, exp, log
from hewmp.parser import parse_text, IntervalParser, DEFAULT_INFLECTIONS, Note, E_INDEX, HZ_INDEX, RAD_INDEX, Tuning, Note, sync_playheads
from hewmp.notation import tokenize_pitch, reverse_inflections, tokenize_interval
from hewmp.smitonic import smitonic_tokenize_interval, SMITONIC_INFLECTIONS, smitonic_tokenize_pitch


def get_notes(text):
    pattern = parse_text(text)[0][0]
    return [note for note in pattern.flatten() if isinstance(note, Note)]


def test_parse_interval():
    mapping = array([12, 19, 28])
    interval_parser = IntervalParser()
    scale = ["P1", "m2", "M2", "m3+", "M3-", "P4", "A4", "P5", "m6+", "M6-", "m7+", "M7-", "P8", "m9", "M9"]
    edo12 = [dot(mapping, interval_parser.parse(s)[0][:len(mapping)]) for s in scale]
    assert edo12 == list(range(15))

    assert (interval_parser.parse("M3-")[0][:3] == array([-2, 0, 1])).all()
    assert (interval_parser.parse("d7+2")[0][:3] == array([7, -1, -2])).all()


def test_parse_pitch():
    mapping = array([12, 19, 28])
    interval_parser = IntervalParser()
    scale = ["C4", "C4#", "D4", "E4b", "F4b", "F4", "G4b", "F4x", "F4#x", "a4", "C5bb", "B4"]
    edo12 = [dot(mapping, interval_parser.parse(s)[0][:len(mapping)]) for s in scale]
    assert edo12 == list(range(-9, 3))

    assert (interval_parser.parse("a-2x<")[0][:4] == array([-34, 16, 0, 1])).all()


def test_transposition():
    pattern_a = parse_text("M2&m2")[0][0]
    pattern_b = parse_text("m3")[0][0]

    for event in pattern_a:
        if isinstance(event, Note):
            note_a = event
    for event in pattern_b:
        if isinstance(event, Note):
            note_b = event

    assert (note_a.pitch == note_b.pitch).all()


def test_transposition_persistence():
    pattern_a = parse_text("M2&M2 M2&M2")[0][0]
    pattern_b = parse_text("M3 M3")[0][0]

    for event in pattern_a:
        if isinstance(event, Note):
            note_a = event
    for event in pattern_b:
        if isinstance(event, Note):
            note_b = event

    assert (note_a.pitch == note_b.pitch).all()


def test_floaty_transposition():
    pattern_a = parse_text("M2&100c M2")[0][0]
    pattern_b = parse_text("M2 M2")[0][0]

    for event in pattern_a:
        if isinstance(event, Note):
            note_a = event
    for event in pattern_b:
        if isinstance(event, Note):
            note_b = event

    assert (note_a.pitch == note_b.pitch).all()


def test_pitch_translation():
    inflections = reverse_inflections(DEFAULT_INFLECTIONS)
    for letter in "aBCDEFG":
        for octave in ("3", "4"):
            for accidental in ("" ,"b", "#", "x"):
                for arrow in ("", "-", "<2", "+2^3"):
                    token = letter + octave + accidental + arrow
                    pitch = IntervalParser().parse(token)[0]
                    retoken = tokenize_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)
                    assert token == retoken


def test_interval_translation():
    inflections = reverse_inflections(DEFAULT_INFLECTIONS)
    for value in range(1, 12):
        qualities = ["dd", "d", "A", "AA"]
        if value in (1, 4, 5, 8, 11):
            qualities.append("P")
        else:
            qualities.extend(["m", "M"])
        for quality in qualities:
            for arrow in ("", "-", "<2", "+2^3"):
                token = "{}{}{}".format(quality, value, arrow)
                pitch = IntervalParser().parse(token)[0]
                retoken = tokenize_interval(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)
                assert token == retoken


def test_smitonic_pitch_translation():
    inflections = reverse_inflections(SMITONIC_INFLECTIONS, basis_indices=(0, 4))
    for letter in "JKNOQRS":
        for octave in ("3", "4"):
            for accidental in ("" ,"b", "#", "x"):
                for arrow in ("", "-", "<2", "+2^3"):
                    token = letter + octave + accidental + arrow
                    pitch = IntervalParser().parse(token)[0]
                    retoken = smitonic_tokenize_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)
                    assert token == retoken


def test_smitonic_interval_translation():
    inflections = reverse_inflections(SMITONIC_INFLECTIONS, basis_indices=(0, 4))
    for value in range(1, 12):
        qualities = ["nn", "n", "W", "WW"]
        if value in (1, 3, 6, 8, 10):
            qualities.append("p")
        else:
            qualities.extend(["s", "L"])
        for quality in qualities:
            for arrow in ("", "-", "<2", "+2^3"):
                token = "{}{}{}".format(quality, value, arrow)
                pitch = IntervalParser().parse(token)[0]
                retoken = smitonic_tokenize_interval(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)
                assert token == retoken


def test_playhead():
    text = """
    P1=M- ~M3- ~P5 | M2=m+ ~m3+ ~P5 |> M2-=m+ ~m3+ ~P5 ||
    """
    pattern = parse_text(text)[0][0]
    start_time, end_time = sync_playheads([pattern])[0]
    data = pattern.realize(start_time=start_time, end_time=end_time).to_json()
    assert Fraction(data["time"]) == 6
    assert Fraction(data["duration"]) == 3
    has_tempo = False
    has_tuning = False
    num_notes = 0
    for event in data["events"]:
        if event["type"] == "tempo":
            has_tempo = True
        if event["type"] == "tuning":
            has_tuning = True
        if event["type"] == "note":
            num_notes += 1
    assert has_tempo
    assert has_tuning
    assert num_notes == 5


def test_split_fifth():
    interval_parser = IntervalParser()
    pitch = interval_parser.parse("P5/2")[0]
    assert (pitch[:2] == array([-0.5, 0.5])).all()
    pitch = interval_parser.parse("3/2")[0]
    assert (pitch[:2] == array([-1, 1])).all()
    pitch = interval_parser.parse("3/2/2")[0]
    assert (pitch[:2] == array([-0.5, 0.5])).all()


def test_double_tone():
    interval_parser = IntervalParser()
    pitch = interval_parser.parse("M2/1*2")[0]
    assert (pitch[:2] == array([-6, 4])).all()


def test_compound():
    interval_parser = IntervalParser()
    pitch = interval_parser.parse("M6")[0]
    assert (pitch[:2] == array([-4, 3])).all()
    pitch = interval_parser.parse("-cM6")[0]
    assert (pitch[:2] == array([3, -3])).all()


def test_pitch_equality():
    text = """
    T:meantone
    @M2 @M2-"""
    pattern = parse_text(text)[0][0].realize()
    tuning = None
    notes = []
    for event in pattern.events:
        if isinstance(event, Tuning):
            tuning = event
        if isinstance(event, Note):
            notes.append(event)
    assert tuning.equals(notes[0].pitch, notes[1].pitch)


def test_otonal():
    text = "4:5:6"
    notes = get_notes(text)
    assert isclose((notes[1].pitch - notes[0].pitch)[:3], [-2, 0, 1]).all()
    assert isclose((notes[2].pitch - notes[0].pitch)[:3], [-1, 1, 0]).all()
    assert isclose((notes[2].pitch - notes[1].pitch)[:3], [1, 1, -1]).all()


def test_utonal():
    text = "6;5;4"
    notes = get_notes(text)
    assert isclose((notes[2].pitch - notes[1].pitch)[:3], [-2, 0, 1]).all()
    assert isclose((notes[2].pitch - notes[0].pitch)[:3], [-1, 1, 0]).all()
    assert isclose((notes[1].pitch - notes[0].pitch)[:3], [1, 1, -1]).all()


def test_added_tone_inversion():
    text = "=M-add2_3"
    notes = get_notes(text)
    assert isclose(notes[0].pitch[:3], [0, 0, 0]).all()
    assert isclose(notes[1].pitch[:3], [-3, 2, 0]).all()
    assert isclose(notes[2].pitch[:3], [-2, 0, 1]).all()
    assert isclose(notes[3].pitch[:3], [-2, 1, 0]).all()


def test_removed_tone():
    text = "=domno3"
    notes = get_notes(text)
    assert isclose(notes[0].pitch[:2], [0, 0]).all()
    assert isclose(notes[1].pitch[:2], [-1, 1]).all()
    assert isclose(notes[2].pitch[:2], [4, -2]).all()


def test_extended_duration():
    text = "P1|[+1]|P5=M-|[+2]||"
    notes = get_notes(text)
    assert notes[0].duration == 2
    assert notes[0].time == 0
    for i in range(1, 4):
        assert notes[i].duration == 3
        assert notes[i].time == 2


def test_stretch_to_logical_duration():
    text = "(P1 M2 M2)[?] P1"
    notes = get_notes(text)
    assert notes[0].duration == 1
    assert notes[0].time == 0
    assert notes[1].duration == 1
    assert notes[1].time == 1
    assert notes[2].duration == 1
    assert notes[2].time == 2
    assert notes[3].duration == 1
    assert notes[3].time == 3


def test_tuplet_hold():
    text = "(P1 ~M3- ~P5 ~P8)[2 ! +1] P1"
    notes = get_notes(text)
    assert notes[0].duration == 3
    assert notes[0].time == 0
    assert notes[1].duration == 2.5
    assert notes[1].time == 0.5
    assert notes[2].duration == 2
    assert notes[2].time == 1
    assert notes[3].duration == 1.5
    assert notes[3].time == 1.5
    assert notes[4].duration == 1
    assert notes[4].time == 3


def test_reverse_time():
    text = "(P1 ~P8 ~P8 ~P8)[R]"
    notes = get_notes(text)
    for i in range(4):
        assert notes[i].duration == 0.25
        assert notes[i].time == 0.75 - 0.25*i
        assert notes[i].pitch[0] == i


def test_absolute_time():
    text = "P1[@2] P8[@0]"
    notes = get_notes(text)
    assert notes[0].duration == 1
    assert notes[0].time == 2
    assert notes[1].duration == 1
    assert notes[1].time == 0


def test_rotate_time():
    text = "(P1 ~P8[2] ~P8[3] ~P8[4])[? >]"
    notes = get_notes(text)
    times_durations = []
    for i in range(4):
        assert notes[i].pitch[0] == (i-1)%4
        times_durations.append((notes[i].time, notes[i].duration))
    assert times_durations == [(0, 4), (4, 1), (5, 2), (7, 3)]


def test_rotate_rhythm():
    text = "(P1 ~P8[2] ~P8[3] ~P8[4])[? ^]"
    notes = get_notes(text)
    times_durations = []
    for i in range(4):
        assert notes[i].pitch[0] == i
        times_durations.append((notes[i].time, notes[i].duration))
    assert times_durations == [(0, 4), (4, 1), (5, 2), (7, 3)]

def test_exponential_rhythm():
    text = "(P1 ~P8 ~P8 ~P8)[e2]"
    notes = get_notes(text)
    denominator = sum(2**i for i in range(4))
    for i in range(4):
        assert notes[i].pitch[0] == i
        assert notes[i].duration * denominator == 2**i
        assert notes[i].time * denominator == 2**i - 1


def test_euclidean_rhythm():
    text = "(P1 ~P8 ~P8 ~P8)[E6 ?]"
    notes = get_notes(text)
    times_durations = []
    for i in range(4):
        assert notes[i].pitch[0] == i
        times_durations.append((notes[i].time, notes[i].duration))
    assert times_durations == [(0, 2), (2, 1), (3, 2), (5, 1)]


def test_mos_rhythm():
    text = "(P1 ~P8 ~P8 ~P8)[5MOS7 ?]"
    notes = get_notes(text)
    times_durations = []
    for i in range(4):
        assert notes[i].pitch[0] == i
        times_durations.append((notes[i].time, notes[i].duration))
    assert times_durations == [(0, 1), (1, 2), (3, 2), (5, 2)]


def test_tuning_optimization():
    text = "T:porcupine"
    pattern = parse_text(text)[0][0]
    for event in pattern:
        if isinstance(event, Tuning):
            tuning = event
    assert(abs(log(16) - tuning.suggested_mapping[0]*4) < 0.006)
    assert(abs(log(9) - tuning.suggested_mapping[1]*2) < 0.006)
    assert(abs(log(5) - tuning.suggested_mapping[2]) < 0.006)


def test_constraints():
    text = "T:porcupine\nC:P8"
    pattern = parse_text(text)[0][0]
    for event in pattern:
        if isinstance(event, Tuning):
            tuning = event
    assert isclose(2, exp(tuning.suggested_mapping[0]))
    error_for_9 = abs(log(9) - tuning.suggested_mapping[1]*2)
    error_for_5 = abs(log(5) - tuning.suggested_mapping[2])
    assert(error_for_9 > 0.006 or error_for_5 > 0.006)


if __name__ == '__main__':
    test_parse_interval()
    test_parse_pitch()
    test_transposition()
    test_transposition_persistence()
    test_floaty_transposition()
    test_pitch_translation()
    test_interval_translation()
    test_smitonic_pitch_translation()
    test_smitonic_interval_translation()
    test_playhead()
    test_split_fifth()
    test_compound()
    test_pitch_equality()
    test_otonal()
    test_utonal()
    test_added_tone_inversion()
    test_removed_tone()
    test_extended_duration()
    test_stretch_to_logical_duration()
    test_tuplet_hold()
    test_reverse_time()
    test_absolute_time()
    test_rotate_time()
    test_rotate_rhythm()
    test_exponential_rhythm()
    test_euclidean_rhythm()
    test_mos_rhythm()
    test_tuning_optimization()
    test_constraints()
