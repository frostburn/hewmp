from fractions import Fraction
from numpy import array, dot, isclose, exp, log
from hewmp.parser import parse_text, IntervalParser, DEFAULT_INFLECTIONS, Note, E_INDEX, HZ_INDEX, RAD_INDEX, Tuning, Note, sync_playheads, Percussion
from hewmp.notation import tokenize_pitch, reverse_inflections, tokenize_interval
from hewmp.smitonic import smitonic_tokenize_interval, SMITONIC_INFLECTIONS, smitonic_tokenize_pitch


def get_notes(text):
    pattern = parse_text(text)[0][0]
    return [note for note in pattern.flatten() if isinstance(note, Note)]


def expect_pitches(notes, pitches):
    assert len(notes) == len(pitches)
    for note, expected in zip(notes, pitches):
        pitch = note.pitch + 0
        pitch[:len(expected)] -= array(expected)
        assert (pitch == 0).all()


def test_parse_interval():
    mapping = array([12, 19, 28])
    interval_parser = IntervalParser()
    scale = ["P1", "m2", "M2", "m3+", "M3-", "P4", "a4", "P5", "m6+", "M6-", "m7+", "M7-", "P8", "m9", "M9"]
    edo12 = [dot(mapping, interval_parser.parse(s).monzo()[:len(mapping)]) for s in scale]
    assert edo12 == list(range(15))

    assert (interval_parser.parse("M3-").monzo()[:3] == array([-2, 0, 1])).all()
    assert (interval_parser.parse("d7+2").monzo()[:3] == array([7, -1, -2])).all()


def test_parse_higher_prime():
    text = "46/27 M6u | 8464/6561 M3u2"
    notes = get_notes(text)
    assert (notes[0].pitch == notes[1].pitch).all()
    assert (notes[2].pitch == notes[3].pitch).all()


def test_parse_pitch():
    mapping = array([12, 19, 28])
    interval_parser = IntervalParser()
    scale = ["C4", "C4#", "D4", "E4b", "F4b", "F4", "G4b", "F4x", "F4#x", "A4", "C5bb", "B4"]
    edo12 = [dot(mapping, interval_parser.parse(s).monzo()[:len(mapping)]) for s in scale]
    assert edo12 == list(range(-9, 3))

    assert (interval_parser.parse("A-2x<").monzo()[:4] == array([-34, 16, 0, 1])).all()


def test_neutral_intervals():
    text = "P5/2 N3 P11/2 N6 m3/2 N2 M13/2 N7"
    notes = get_notes(text)
    assert (notes[0].pitch == notes[1].pitch).all()
    assert (notes[2].pitch == notes[3].pitch).all()
    assert (notes[4].pitch == notes[5].pitch).all()
    assert (notes[6].pitch == notes[7].pitch).all()


def test_bonus_intervals():
    text = "m9/2 hd5 M7/2 ha4 d15/2 hd8 a1/2 ha1"
    notes = get_notes(text)
    assert (notes[0].pitch == notes[1].pitch).all()
    assert (notes[2].pitch == notes[3].pitch).all()
    assert (notes[4].pitch == notes[5].pitch).all()
    assert (notes[6].pitch == notes[7].pitch).all()


def test_half_sharps():
    text = "A4&N3 C5t C4&N3 E4d A4&N6 F5t"
    notes = get_notes(text)
    assert (notes[0].pitch == notes[1].pitch).all()
    assert (notes[2].pitch == notes[3].pitch).all()
    assert (notes[4].pitch == notes[5].pitch).all()


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
    for letter in "ABCDEFG":
        for octave in ("3", "4"):
            for accidental in ("" ,"b", "#", "x"):
                for arrow in ("", "-", "<2", "+2^3", "u4", "n"):
                    token = letter + octave + accidental + arrow
                    pitch = IntervalParser().parse(token).monzo()
                    retoken = tokenize_pitch(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)
                    assert token == retoken


def test_interval_translation():
    inflections = reverse_inflections(DEFAULT_INFLECTIONS)
    for value in range(1, 12):
        qualities = ["dd", "d", "a", "aa"]
        if value in (1, 4, 5, 8, 11):
            qualities.append("P")
        else:
            qualities.extend(["m", "M"])
        for quality in qualities:
            for arrow in ("", "-", "<2", "+2^3"):
                token = "{}{}{}".format(quality, value, arrow)
                pitch = IntervalParser().parse(token).monzo()
                retoken = tokenize_interval(pitch, inflections, E_INDEX, HZ_INDEX, RAD_INDEX)
                assert token == retoken


def test_chords():
    text = "=hdim"
    notes = get_notes(text)
    pitches = [[0], [1, 1, -1], [2, 2, -2], [0, 2, -1]]
    expect_pitches(notes, pitches)

    text = "=sus4"
    notes = get_notes(text)
    pitches = [[0], [2, -1], [-1, 1]]
    expect_pitches(notes, pitches)


def test_smitonic_pitch_translation():
    inflections = reverse_inflections(SMITONIC_INFLECTIONS, basis_indices=(0, 4))
    for letter in "JKOQSUY":
        for octave in ("3", "4"):
            for accidental in ("" ,"b", "#", "x"):
                for arrow in ("", "-", "<2", "+2^3"):
                    token = letter + octave + accidental + arrow
                    pitch = IntervalParser().parse(token).monzo()
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
                pitch = IntervalParser().parse(token).monzo()
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
    pitch = interval_parser.parse("P5/2").monzo()
    assert (pitch[:2] == array([-0.5, 0.5])).all()
    pitch = interval_parser.parse("3/2").monzo()
    assert (pitch[:2] == array([-1, 1])).all()
    pitch = interval_parser.parse("3/2/2").monzo()
    assert (pitch[:2] == array([-0.5, 0.5])).all()


def test_double_tone():
    interval_parser = IntervalParser()
    pitch = interval_parser.parse("M2/1*2").monzo()
    assert (pitch[:2] == array([-6, 4])).all()


def test_compound():
    interval_parser = IntervalParser()
    pitch = interval_parser.parse("M6").monzo()
    assert (pitch[:2] == array([-4, 3])).all()
    pitch = interval_parser.parse("-cM6").monzo()
    assert (pitch[:2] == array([3, -3])).all()
    pitch = interval_parser.parse("`M6").monzo()
    assert (pitch[:2] == array([-5, 3])).all()


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


def test_tuplets():
    text = "(P1 ~P8) (~P8 ~P8 ~P8) (~P8 ~P8)[2] (~P8[2] ~P8) ~P8"
    notes = get_notes(text)
    times_durations = [
        (0, Fraction(1, 2)),
        (Fraction(1, 2), Fraction(1, 2)),
        (1, Fraction(1, 3)),
        (Fraction(4, 3), Fraction(1, 3)),
        (Fraction(5, 3), Fraction(1, 3)),
        (2, 1),
        (3, 1),
        (4, Fraction(2, 3)),
        (Fraction(14, 3), Fraction(1, 3)),
        (5, 1),
    ]
    for i in range(len(notes)):
        assert notes[i].pitch[0] == i
        assert notes[i].time == times_durations[i][0]
        assert notes[i].duration == times_durations[i][1]


def test_extended_duration():
    text = "P1|[!1]|P5=M-|[!2]||"
    notes = get_notes(text)
    assert notes[0].duration == 2
    assert notes[0].time == 0
    for i in range(1, 4):
        assert notes[i].duration == 3
        assert notes[i].time == 2


def test_extend_duration_without_advancing_time():
    text = "P1[~1] P8"
    notes = get_notes(text)
    assert notes[0].duration == 2
    assert notes[0].time == 0
    assert notes[1].duration == 1
    assert notes[1].time == 1


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
    text = "(P1 ~M3- ~P5 ~P8)[2 ~ !1] P1"
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
    text = "(P1 ~P8 ~P8 ~P8)[CG2]"
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

    text = "(P1 P8)[E5 ?]"
    notes = get_notes(text)
    assert notes[0].time == 0
    assert notes[1].time == 2

    text = "(P1 P8)[1E5 ?]"
    notes = get_notes(text)
    assert notes[0].time == 0
    assert notes[1].time == 3


def test_mos_rhythm():
    text = "(P1 ~P8 ~P8 ~P8)[7PG5 ?]"
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


def test_basic_color_notation():
    text = """
        1/1 w1
        21/20 zg2
        16/15 g2
        10/9 y2
        9/8 w2
        8/7 r2
        7/6 z3
        32/27 w3
        6/5 g3
        5/4 y3
        9/7 r3
        21/16 z4
        4/3 w4
        27/20 g4
        7/5 zg5
        45/32 y4
        64/45 g5
        10/7 ry4
        40/27 y5
        3/2 w5
        32/21 r5
        14/9 z6
        8/5 g6
        5/3 y6
        27/16 w6
        12/7 r6
        7/4 z7
        16/9 w7
        9/5 g7
        15/8 y7
        40/21 ry7
        2/1 w8
    """
    notes = get_notes(text)
    assert len(notes) == 64
    for i in range(32):
        assert (notes[2*i].pitch == notes[2*i + 1].pitch).all()


def test_color_exponents():
    text = "y3 yy3 y^33 y⁴3 y³⁴3"
    notes = get_notes(text)
    monzos = [[-2, 0, 1], [2, -4, 2], [-5, -1, 3], [-1, -5, 4], [-24, -34, 34]]
    for note, monzo in zip(notes, monzos):
        assert list(note.pitch[:3]) == monzo


def test_higher_prime_color_notation():
    text = "1o4 3o6 17u7 19o3 23u2"
    notes = get_notes(text)
    monzos = [[-3, 0, 0, 0, 1], [-3, 0, 0, 0, 0, 1], [5, 0, 0, 0, 0, 0, -1], [-4, 0, 0, 0, 0, 0, 0, 1], [0, 3, 0, 0, 0, 0, 0, 0, -1]]
    for note, monzo in zip(notes, monzos):
        assert list(note.pitch[:len(monzo)]) == monzo


def test_higher_prime_color_repeats():
    text = "1oo4 19oo³6"
    notes = get_notes(text)
    assert (notes[0].pitch[:5] == [-8, 1, 0, 0, 2]).all()
    assert (notes[1].pitch[:8] == [-14, -7, 0, 0, 0, 0, 0, 6]).all()


def test_large_small_color_notation():
    text = "w3 Lw3 sw3 LLw3 s⁴w3"
    notes = get_notes(text)
    monzos = [[5, -3], [-6, 4], [16, -10], [-17, 11], [49, -31]]
    for note, monzo in zip(notes, monzos):
        assert list(note.pitch[:2]) == monzo


def test_wa_comma():
    text = "-ssw2 LLw-2"
    notes = get_notes(text)
    for note in notes:
        assert note.pitch[0] == -19
        assert note.pitch[1] == 12
        assert (note.pitch[2:] == 0).all()


def test_po_qu():
    text = "ry1 ryp2"
    notes = get_notes(text)
    assert (notes[0].pitch == notes[1].pitch).all()

    text = "zz2 zzq1"
    notes = get_notes(text)
    assert (notes[0].pitch == notes[1].pitch).all()


def test_harmonic_chord():
    text = "=ht31"
    notes = get_notes(text)
    odds = [
        [0],
        [0, 1],
        [0, 0, 1],
        [0, 0, 0, 1],
        [0, 2],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 1],
        [0, 1, 1],
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 1, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 2],
        [0, 3],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    ]
    expect_pitches(notes, odds)

    text = "=hf9+15no5\\4"
    notes = get_notes(text)
    pitches = [[0], [2, -1], [-2, 0, 0, 1], [1], [-2, 2], [-2, 1, 1]]
    expect_pitches(notes, pitches)


def test_subharmonic_chord():
    text = "=st9"
    notes = get_notes(text)
    pitches = [[0], [0, 2, 0, -1], [0, 2, -1], [0, 1], [0, 2]]
    expect_pitches(notes, pitches)

    text = "=sf10"
    notes = get_notes(text)
    pitches = [[0], [1, -2, 1], [-2, 0, 1], [1, 0, 1, -1], [0, -1, 1], [1], [-1, 0, 1]]
    expect_pitches(notes, pitches)


def test_color_chord():
    text = "=y"
    notes = get_notes(text)
    pitches = [[0], [-2, 0, 1], [-1, 1]]
    expect_pitches(notes, pitches)

    text = "=z"
    notes = get_notes(text)
    pitches = [[0], [-1, -1, 0, 1], [-1, 1]]
    expect_pitches(notes, pitches)

    text = "=Lw"
    notes = get_notes(text)
    pitches = [[0], [-6, 4], [-1, 1]]
    expect_pitches(notes, pitches)

    text = "=r+ry4no5"
    notes = get_notes(text)
    pitches = [[0], [0, 2, 0, -1], [1, 0, 1, -1]]
    expect_pitches(notes, pitches)

    text = "=L3oo1u11+w4\\g5no7"
    notes = get_notes(text)
    pitches = [[0], [-10, 4, 0, 0, -1, 2], [2, -1], [6, -2, -1], [-2, 2], [-12, 6, 0, 0, -1, 2]]
    expect_pitches(notes, pitches)

    text = "C4=y6 wC4 yE4 wG4 yA4"
    notes = get_notes(text)
    for i in range(4):
        assert (notes[i].pitch == notes[i+4].pitch).all()

    text = "=g+y6\\gg5"
    notes = get_notes(text)
    pitches =  [[0], [1, 1, -1], [2, 2, -2], [0, -1, 1]]
    expect_pitches(notes, pitches)

    text = "=y+w7"
    notes = get_notes(text)
    pitches = [[0], [-2, 0, 1], [-1, 1], [4, -2]]
    expect_pitches(notes, pitches)

    text = "=5"
    notes = get_notes(text)
    pitches = [[0], [-1, 1]]
    expect_pitches(notes, pitches)

    text = "=zg5"  # TODO: Document how the logic differs from C(zg5)
    notes = get_notes(text)
    pitches = [[0], [0, 0, -1, 1]]
    expect_pitches(notes, pitches)

    text = "=zg5+z7"
    notes = get_notes(text)
    pitches = [[0], [0, 0, -1, 1], [-2, 0, 0, 1]]
    expect_pitches(notes, pitches)


def test_color_chord_po():
    text = "=y7+ry8"  # TODO: Document why y7ry8 is not supported
    notes = get_notes(text)
    pitches = [[0], [-2, 0, 1], [-1, 1], [-3, 1, 1], [0, 1, 1, -1]]
    expect_pitches(notes, pitches)

    text = "=y7+ryp9"
    notes = get_notes(text)
    expect_pitches(notes, pitches)


def test_color_pitches():
    text = "A4 gB4 yC#5 zgD5 1oE5 3uuF5 Gb5 A♮5"
    notes = get_notes(text)
    pitches = [[0], [-7, 6, -1], [-2, 0, 1], [-8, 5, -1, 1], [-6, 2, 0, 0, 1], [5, 2, 0, 0, 0, -2], [15, -9], [1]]
    expect_pitches(notes, pitches)


def test_color_roman():
    text = "I=y yIII=g V=y+7 I=y+8"
    notes = get_notes(text)
    chords = [
        [[0], [-2, 0, 1], [-1, 1]],
        [[-2, 0, 1], [-1, 1], [-3, 1, 1]],
        [[-1, 1], [-3, 1, 1], [-2, 2], [3, -1]],
        [[0], [-2, 0, 1], [-1, 1], [1]],
    ]
    for note in notes:
        i = int(note.time)
        for expected in chords[i]:
            if (note.pitch[:len(expected)] == expected).all():
                break
        else:
            assert False


def test_ups_and_downs_tritone():
    text = "^1 v8"
    notes = get_notes(text)
    pitches = [[0.5], [0.5]]
    expect_pitches(notes, pitches)


def test_ups_and_downs_scale():
    text = "ET:18b\nA4 ^A4 B4 ^B4 Bb4 vC5 C5 ^C5 @P4 @^P4 @P5 @^5 @M6 @N6 @m6 @hd6 ^1 M2"
    notes = get_notes(text)
    assert (notes[1].pitch[:2] == [-1.5, 1]).all()
    assert len(notes) == 18
    mapping = array([18, 28])
    for i, note in enumerate(notes):
        assert dot(mapping, note.pitch[:len(mapping)]) == i


def test_ups_and_downs_wendy():
    text = "ET:alpha\n1\\ ^A4"
    notes = get_notes(text)
    assert isclose(notes[0].pitch, notes[1].pitch).all()


def test_rest():
    text = "1 1 . 1 .. 1 ... 1"
    notes = get_notes(text)
    times = []
    for note in notes:
        assert note.duration == 1
        times.append(note.time)
    assert times == [0, 1, 3, 6, 10]


def test_pedal():
    text = "1 1 ! 1 !! 1 !!! 1"
    notes = get_notes(text)
    durations = []
    times = []
    for note in notes:
        durations.append(note.duration)
        times.append(note.time)
    assert durations == [1, 2, 3, 4, 1]
    assert times == [0, 1, 3, 6, 10]


def test_repeat():
    text = "(A4,C5)[3] % %!"
    notes = get_notes(text)
    durations = []
    times = []
    for note in notes:
        durations.append(note.duration)
        times.append(note.time)
    assert durations == [3, 3, 1, 1, 2, 2]
    assert times == [0, 0, 3, 3, 4, 4]


def test_up_down_chords():
    text = "ET:19\n=vM"
    notes = get_notes(text)
    pitches = [[0], [5, -3], [-1, 1]]
    expect_pitches(notes, pitches)

    text = "ET:19\n=^m7"
    notes = get_notes(text)
    pitches = [[0], [-6, 4], [-1, 1], [-7, 5]]
    expect_pitches(notes, pitches)


def test_complex_voicing():
    text = "=y7_5R7351"
    notes = get_notes(text)
    pitches = [[0], [-1, 0, 1], [0, 1], [-3, 1, 1], [2], [-2, 1]]
    expect_pitches(notes, pitches)

    text = "=m+_315R5"
    notes = get_notes(text)
    pitches = [[0], [-1, 1, -1], [-1, 1], [-1], [-2, 1]]
    expect_pitches(notes, pitches)


def test_flavor_chord_ups_and_downs():
    text = "ET:12\n=^7-"
    notes = get_notes(text)
    pitches = [[0], [6, -5, 1], [-1, 1], [-8, 7, -1]]
    expect_pitches(notes, pitches)


def test_percussion_chaining():
    text = "N:percussion\nkh.sh%kh!sho"
    pattern = parse_text(text)[0][0]
    expected = [
        ("Acoustic Bass Drum", 0, 1),
        ("Closed Hi-hat", 1, 1),
        ("Acoustic Snare", 3, 1),
        ("Closed Hi-hat", 4, 1),
        ("Closed Hi-hat", 5, 1),
        ("Acoustic Bass Drum", 6, 1),
        ("Closed Hi-hat", 7, 2),
        ("Acoustic Snare", 9, 1),
        ("Closed Hi-hat", 10, 1),
        ("Open Hi-hat", 11, 1),
    ]

    for event in pattern:
        if isinstance(event, Percussion):
            name, time, duration = expected.pop(0)
            assert event.name == name
            assert event.time == time
            assert event.duration == duration


if __name__ == '__main__':
    test_parse_interval()
    test_parse_higher_prime()
    test_parse_pitch()
    test_neutral_intervals()
    test_bonus_intervals()
    test_half_sharps()
    test_transposition()
    test_transposition_persistence()
    test_floaty_transposition()
    test_pitch_translation()
    test_interval_translation()
    test_chords()
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
    test_tuplets()
    test_extended_duration()
    test_extend_duration_without_advancing_time()
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
    test_basic_color_notation()
    test_color_exponents()
    test_higher_prime_color_notation()
    test_higher_prime_color_repeats()
    test_large_small_color_notation()
    test_wa_comma()
    test_po_qu()
    test_harmonic_chord()
    test_subharmonic_chord()
    test_color_chord()
    test_color_chord_po()
    test_color_pitches()
    test_color_roman()
    test_ups_and_downs_tritone()
    test_ups_and_downs_scale()
    test_ups_and_downs_wendy()
    test_rest()
    test_pedal()
    test_repeat()
    test_up_down_chords()
    test_complex_voicing()
    test_flavor_chord_ups_and_downs()
    test_percussion_chaining()
