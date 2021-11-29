from fractions import Fraction
from numpy import array, dot
from hewmp_parser import parse_text, parse_interval, DEFAULT_INFLECTIONS, Note, E_INDEX, HZ_INDEX, RAD_INDEX
from notation import notate_pitch, reverse_inflections, notate_interval


def test_parse_interval():
    mapping = array([12, 19, 28])
    scale = ["P1", "m2", "M2", "m3+", "M3-", "P4", "A4", "P5", "m6+", "M6-", "m7+", "M7-", "P8", "m9", "M9"]
    edo12 = [dot(mapping, parse_interval(s, DEFAULT_INFLECTIONS, 12, 2)[0][:len(mapping)]) for s in scale]
    assert edo12 == list(range(15))

    assert (parse_interval("M3-", DEFAULT_INFLECTIONS, 12, 2)[0][:3] == array([-2, 0, 1])).all()
    assert (parse_interval("d7+2", DEFAULT_INFLECTIONS, 12, 2)[0][:3] == array([7, -1, -2])).all()


def test_parse_pitch():
    mapping = array([12, 19, 28])
    scale = ["C4", "C4#", "D4", "E4b", "F4b", "F4", "G4b", "F4x", "F4#x", "a4", "C5bb", "B4"]
    edo12 = [dot(mapping, parse_interval(s, DEFAULT_INFLECTIONS, 12, 2)[0][:len(mapping)]) for s in scale]
    assert edo12 == list(range(-9, 3))

    assert (parse_interval("a-2x<", DEFAULT_INFLECTIONS, 12, 2)[0][:4] == array([-34, 16, 0, 1])).all()


def test_transposition():
    pattern_a = parse_text("M2&m2")
    pattern_b = parse_text("m3")

    for event in pattern_a:
        if isinstance(event, Note):
            note_a = event
    for event in pattern_b:
        if isinstance(event, Note):
            note_b = event

    assert (note_a.pitch == note_b.pitch).all()


def test_transposition_persistence():
    pattern_a = parse_text("M2&M2 M2&M2")
    pattern_b = parse_text("M3 M3")

    for event in pattern_a:
        if isinstance(event, Note):
            note_a = event
    for event in pattern_b:
        if isinstance(event, Note):
            note_b = event

    assert (note_a.pitch == note_b.pitch).all()


def test_floaty_transposition():
    pattern_a = parse_text("M2&~100c M2")
    pattern_b = parse_text("M2 M2")

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
                    pitch = parse_interval(token, DEFAULT_INFLECTIONS, 12, 2)[0]
                    retoken = notate_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)
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
                pitch = parse_interval(token, DEFAULT_INFLECTIONS, 12, 2)[0]
                retoken = notate_interval(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)
                assert token == retoken


def test_playhead():
    text = """
    P1=M- ~M3- ~P5 | M2=m+ ~m3+ ~P5 |> M2-=m+ ~m3+ ~P5 ||
    """
    pattern = parse_text(text)
    data = pattern.to_json()
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
    pitch = parse_interval("P5/2", DEFAULT_INFLECTIONS, 12, 0)[0]
    assert (pitch[:2] == array([-0.5, 0.5])).all()
    pitch = parse_interval("3/2", DEFAULT_INFLECTIONS, 12, 0)[0]
    assert (pitch[:2] == array([-1, 1])).all()
    pitch = parse_interval("3/2/2", DEFAULT_INFLECTIONS, 12, 0)[0]
    assert (pitch[:2] == array([-0.5, 0.5])).all()


def test_compound():
    pitch = parse_interval("M6", DEFAULT_INFLECTIONS, 12, 0)[0]
    assert (pitch[:2] == array([-4, 3])).all()
    pitch = parse_interval("-cM6", DEFAULT_INFLECTIONS, 12, 0)[0]
    assert (pitch[:2] == array([3, -3])).all()


if __name__ == '__main__':
    test_parse_interval()
    test_parse_pitch()
    test_transposition()
    test_transposition_persistence()
    test_floaty_transposition()
    test_pitch_translation()
    test_interval_translation()
    test_playhead()
    test_split_fifth()
    test_compound()
