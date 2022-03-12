from .util import Splitter
from . import orgone


ARROWS = "+-><^vunUDAVMWi!*%"
OPPOSITE = {}
for i in range(0, len(ARROWS), 2):
    OPPOSITE[ARROWS[i]] = ARROWS[i+1]
    OPPOSITE[ARROWS[i+1]] = ARROWS[i]


ADDED_QUALITIES = {
    1: "P",
    2: "M",
    3: "M",
    4: "P",
    5: "P",
    6: "M",
    7: "M",
}


def separate_by_arrows(token):
    separated = []
    current_arrow_token = ""
    for character in token:
        if character in ARROWS:
            separated.append(current_arrow_token)
            current_arrow_token = ""
        current_arrow_token += character
    separated.append(current_arrow_token)
    return separated


def accidental_to_quality(token):
    separated = separate_by_arrows(token)
    base = separated.pop(0)
    if base[0] in "b#":
        interval_class = int(base[1:])
    else:
        interval_class = int(base)
    quality = ADDED_QUALITIES[1 + (interval_class-1)%7]
    if base[0] == "b":
        if quality == "M":
            quality = "m"
        else:
            quality = "d"
    if base[0] == "#":
        quality = "a"
    return "{}{}{}".format(quality, interval_class, "".join(separated))


FLAVOR_CHORDS = {
    "m6": (("P1", 0), ("m3", 1), ("P5", 0), ("M6", -1)),

    "7": (("P1", 0), ("M3", 1), ("P5", 0), ("m7", -1)),

    "mM7": (("P1", 0), ("m3", 1), ("P5", 0), ("M7", -1)),

    "m6/9": (("P1", 0), ("m3", 1), ("P5", 0), ("M6", -1), ("M9", 0)),

    "9": (("P1", 0), ("M3", 1), ("P5", 0), ("m7", -1), ("M9", 0)),

    "11": (("P1", 0), ("M3", 1), ("P5", 0), ("m7", -1), ("M9", 0), ("P11", 0)),

    "#11": (("P1", 0), ("M3", 1), ("P5", 0), ("m7", -1), ("M9", 0), ("a11", 0)),

    "13": (("P1", 0), ("M3", 1), ("P5", 0), ("m7", -1), ("M9", 0), ("P11", 0), ("M13", 0)),

    "o": (("P1", 0), ("m3", 1), ("d5", 2)),
    "o7": (("P1", 0), ("m3", 1), ("d5", 2), ("d7", 3)),

    "ø": (("P1", 0), ("m3", 1), ("d5", 2), ("m7", 1)),

    "hdom": (("P1", 0), ("m3", 1), ("d5", 2), ("m7", 0)),

    "aug": (("P1", 0), ("M3", 1), ("a5", 2)),
    "aug7": (("P1", 0), ("M3", 1), ("a5", 2), ("a7", 3)),

    "haug": (("P1", 0), ("M3", 1), ("a5", 2), ("m7", -1)),

    "augdom": (("P1", 0), ("M3", 1), ("a5", 2), ("m7", 0)),

    "M7aug": (("P1", 0), ("M3", 1), ("a5", 2), ("M7", 1)),
}

FLAVOR_CHORDS["dim"] = FLAVOR_CHORDS["o"]
FLAVOR_CHORDS["dim7"] = FLAVOR_CHORDS["o7"]

FLAVOR_CHORDS["hdim"] = FLAVOR_CHORDS["ø"]
FLAVOR_CHORDS["ø7"] = FLAVOR_CHORDS["ø"]
FLAVOR_CHORDS["hdim7"] = FLAVOR_CHORDS["ø"]

FLAVOR_CHORDS["haug7"] = FLAVOR_CHORDS["haug"]

def make_flavor_chord(base, arrow_tokens, ups_and_downs):
    positive_inflection = "".join(arrow_tokens)
    negative_inflection = ""

    for arrow_token in arrow_tokens:
        negative_inflection += OPPOSITE[arrow_token[0]] + arrow_token[1:]

    downs_and_ups = ""
    for arrow in ups_and_downs:
        if arrow == "^":
            downs_and_ups += "v"
        if arrow == "v":
            downs_and_ups += "^"
        if arrow == ">":
            downs_and_ups += "<"
        if arrow == "<":
            downs_and_ups += ">"

    chord = []
    for interval, flavor in FLAVOR_CHORDS[base]:
        while flavor > 0:
            interval = ups_and_downs + interval + positive_inflection
            flavor -= 1
        while flavor < 0:
            interval = downs_and_ups + interval + negative_inflection
            flavor += 1
        chord.append(interval)

    return chord


BASIC_CHORDS = {
    "M": (("P1", "M3", "P5"), (1,)),
    "m": (("P1", "m3", "P5"), (1,)),

    "6": (("P1", "M3", "P5", "M6"), (1, 3)),
    "mb6": (("P1", "m3", "P5", "m6"), (1, 3)),

    "M7": (("P1", "M3", "P5", "M7"), (1, 3)),
    "m7": (("P1", "m3", "P5", "m7"), (1, 3)),
    "dom": (("P1", "M3", "P5", "m7"), (1,)),

    "6/9": (("P1", "M3", "P5", "M6", "M9"), (1, 3, 4)),
    "mb6b9": (("P1", "m3", "P5", "m6", "m9"), (1, 3, 4)),

    "M9": (("P1", "M3", "P5", "M7", "M9"), (1, 3)),
    "m9": (("P1", "m3", "P5", "m7", "M9"), (1, 3)),
    "mb9": (("P1", "m3", "P5", "m7", "m9"), (1, 3, 4)),
    "dom9": (("P1", "M3", "P5", "m7", "M9"), (1,)),
    "domb9": (("P1", "M3", "P5", "m7", "m9"), (1,)),

    "M11": (("P1", "M3", "P5", "M7", "M9", "P11"), (1, 3, 5)),
    "m11": (("P1", "m3", "P5", "m7+", "M9", "P11"), (1, 3, 5)),
    "M#11": (("P1", "M3", "P5", "M7", "M9", "a11"), (1, 3, 5)),
    "dom11": (("P1", "M3", "P5", "m7", "M9", "P11"), (1,)),

    "domb12": (("P1", "M3-", "P5", "m7", "M9", "d12"), (1,)),

    "M13": (("P1", "M3", "P5", "M7", "M9", "M13"), (1, 3, 5)),
    "dom13": (("P1", "M3-", "P5", "m7", "M9", "M13"), (1,)),

    "M#15": (("P1", "M3", "P5", "M7", "M9", "M13", "a15"), (1, 3, 5)),
}


SUS_CHORDS = {
    "sus2": (("P1", "M2", "P5"), (1,)),
    "sus4": (("P1", "P4", "P5"), (1,)),
    "quartal": (("P1", "P4", "m7"), (1, 2)),
    "quintal": (("P1", "P5", "M9"), (2,)),
}


BASIC_CHORDS_ = {}
BASIC_CHORDS_.update(BASIC_CHORDS)
BASIC_CHORDS_.update(SUS_CHORDS)


def make_basic_chord(base, arrow_tokens, ups_and_downs, chords=BASIC_CHORDS_):
    inflection = "".join(arrow_tokens)
    intervals, inflection_indices = chords[base]
    chord = []
    for i, interval in enumerate(intervals):
        if i in inflection_indices:
            chord.append(ups_and_downs + interval + inflection)
        else:
            chord.append(interval)
    return chord


def split_interval(token):
    ups_and_downs = 0
    lifts_and_drops = 0
    while token[0] in "^v><":
        if token[0] == "^":
            ups_and_downs += 1
        if token[0] == "v":
            ups_and_downs -= 1
        if token[0] == ">":
            lifts_and_drops += 1
        if token[0] == "<":
            lifts_and_drops -= 1
        token = token[1:]
    quality = ""
    while not token[0].isdigit():
        quality += token[0]
        token = token[1:]
    value = ""
    while token and token[0].isdigit():
        value += token[0]
        token = token[1:]
    value = int(value)
    return quality, value, ups_and_downs, lifts_and_drops, token


QUALITY_RANKING = ["nn", "dd", "n", "d", "s", "m", "P", "M", "L", "a", "W", "aa", "WW"]
def interval_key(token):
    quality, value, ups_and_downs, lifts_and_drops, token = split_interval(token)
    return (value, QUALITY_RANKING.index(quality), ups_and_downs, lifts_and_drops, token)


TONE_SPLITTER = Splitter(("add", "no", "sus"))

PROTECTED_PREFIXES = ["M", "d", "u", "su", "aug", "qua", "qui", "hdim", "haug", "M7aug"]
PROTECTED_PREFIXES.sort(key=lambda x: -len(x))

def expand_chord(token):
    notation = "hewmp"
    ups_and_downs = ""
    while token[0] in "^v><":
        ups_and_downs += token[0]
        token = token[1:]

    token, tones = TONE_SPLITTER(token)
    added_intervals = list(map(accidental_to_quality, tones["add"]))
    removed_tones = [int(tone) for tone in tones["no"]]
    sus_replacement = None
    for replacement in tones["sus"]:
        if not token:
            token = "sus{}".format(replacement)
        else:
            sus_replacement = accidental_to_quality(replacement)

    prefix = ""
    for protected in PROTECTED_PREFIXES:
        if token.startswith(protected):
            prefix = protected
            token = token[len(prefix):]
            break

    separated = separate_by_arrows(token)
    base = prefix + separated.pop(0)

    chord = None

    if base in FLAVOR_CHORDS:
        chord = make_flavor_chord(base, separated, ups_and_downs)
    if base in BASIC_CHORDS:
        chord = make_basic_chord(base, separated, ups_and_downs)
    if base in orgone.BASIC_CHORDS:
        chord = make_basic_chord(base, separated, ups_and_downs, chords=orgone.BASIC_CHORDS)
        notation = "orgone"
    if sus_replacement is not None:
        if chord is None:
            raise ValueError("Sus replacement on an incompatible chord")
        chord[1] = sus_replacement
    if base in SUS_CHORDS:
        chord = make_basic_chord(base, separated, ups_and_downs)

    if chord is None:
        raise ValueError("Unrecognized chord {}".format(base))

    result = sorted(chord + added_intervals, key=interval_key)
    for tone in removed_tones:
        for chord_tone in result[:]:
            _, value, _, _ , _ = split_interval(chord_tone)
            if value == tone:
                result.remove(chord_tone)
    return result, notation
