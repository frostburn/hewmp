from numpy import array, dot
from hewmp_parser import parse_text, parse_interval, DEFAULT_INFLECTIONS, Note


def test_parse_interval():
    mapping = array([12, 19, 28])
    scale = ["P1", "m2", "M2", "m3+", "M3-", "P4", "A4", "P5", "m6+", "M6-", "m7+", "M7-", "P8", "m9", "M9"]
    edo12 = [dot(mapping, parse_interval(s, DEFAULT_INFLECTIONS, 12, 2)[0][:len(mapping)]) for s in scale]
    assert edo12 == list(range(15))

    assert (parse_interval("M3-", DEFAULT_INFLECTIONS, 12, 2)[0][:3] == array([-2, 0, 1])).all()
    assert (parse_interval("d7+2", DEFAULT_INFLECTIONS, 12, 2)[0][:3] == array([7, -1, -2])).all()


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


if __name__ == '__main__':
    test_parse_interval()
    test_transposition()
    test_transposition_persistence()
    test_floaty_transposition()
