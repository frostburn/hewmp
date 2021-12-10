from fractions import Fraction
from numpy import array, dot, isclose
from hewmp.parser import parse_text, IntervalParser, DEFAULT_INFLECTIONS, Note, E_INDEX, HZ_INDEX, RAD_INDEX, RealTuning, GatedNote
from hewmp.notation import tokenize_pitch, reverse_inflections, tokenize_interval
from hewmp.smitonic import smitonic_tokenize_interval, SMITONIC_INFLECTIONS, smitonic_tokenize_pitch


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
    pattern_a = parse_text("M2&m2")[0]
    pattern_b = parse_text("m3")[0]

    for event in pattern_a:
        if isinstance(event, Note):
            note_a = event
    for event in pattern_b:
        if isinstance(event, Note):
            note_b = event

    assert (note_a.pitch == note_b.pitch).all()


def test_transposition_persistence():
    pattern_a = parse_text("M2&M2 M2&M2")[0]
    pattern_b = parse_text("M3 M3")[0]

    for event in pattern_a:
        if isinstance(event, Note):
            note_a = event
    for event in pattern_b:
        if isinstance(event, Note):
            note_b = event

    assert (note_a.pitch == note_b.pitch).all()


def test_floaty_transposition():
    pattern_a = parse_text("M2&~100c M2")[0]
    pattern_b = parse_text("M2 M2")[0]

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
    pattern = parse_text(text)[0]
    data = pattern.realize().to_json()
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
    pattern = parse_text(text)[0].realize()
    tuning = None
    notes = []
    for event in pattern.events:
        if isinstance(event, RealTuning):
            tuning = event
        if isinstance(event, GatedNote):
            notes.append(event)
    assert tuning.equals(notes[0].pitch, notes[1].pitch)


def test_otonal():
    text = "4:5:6"
    pattern = parse_text(text)[0]
    notes = [note for note in pattern.flatten() if isinstance(note, Note)]
    assert isclose((notes[1].pitch - notes[0].pitch)[:3], [-2, 0, 1]).all()
    assert isclose((notes[2].pitch - notes[0].pitch)[:3], [-1, 1, 0]).all()
    assert isclose((notes[2].pitch - notes[1].pitch)[:3], [1, 1, -1]).all()


def test_utonal():
    text = "6;5;4"
    pattern = parse_text(text)[0]
    notes = [note for note in pattern.flatten() if isinstance(note, Note)]
    assert isclose((notes[2].pitch - notes[1].pitch)[:3], [-2, 0, 1]).all()
    assert isclose((notes[2].pitch - notes[0].pitch)[:3], [-1, 1, 0]).all()
    assert isclose((notes[1].pitch - notes[0].pitch)[:3], [1, 1, -1]).all()


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
