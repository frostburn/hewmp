ARROWS = "+-><^vudUDAVMWi!*%"
OPPOSITE = {}
for i in range(0, len(ARROWS), 2):
    OPPOSITE[ARROWS[i]] = ARROWS[i+1]
    OPPOSITE[ARROWS[i+1]] = ARROWS[i]

# TODO
EXTRA_CHORDS = {
    "o": ["P1", "m3+", "d5+2"],
}

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
        quality = "A"
    return "{}{}{}".format(quality, interval_class, "".join(separated))


# TODO
FLAVOR_CHORDS = {
    "7": (("P1", 0), ("M3", 1), ("P5", 0), ("m7", -1)),
}

def make_flavor_chord(base, arrow_tokens):
    positive_inflection = "".join(arrow_tokens)
    negative_inflection = ""

    for arrow_token in arrow_tokens:
        negative_inflection += OPPOSITE[arrow_token[0]] + arrow_token[1:]

    chord = []
    for interval, flavor in FLAVOR_CHORDS[base]:
        if flavor > 0:
            interval += positive_inflection
        if flavor < 0:
            interval += negative_inflection
        chord.append(interval)

    return chord

# TODO
BASIC_CHORDS = {
    "M": (("P1", "M3", "P5"), (1,)),
    "dom": (("P1", "M3", "P5", "m7"), (1,)),
    "m7": (("P1", "m3", "P5", "m7"), (1, 3)),
}

# TODO
SUS_CHORDS = {
    "sus2": (("P1", "M2", "P5"), (1,)),
}

BASIC_CHORDS_ = {}
BASIC_CHORDS_.update(BASIC_CHORDS)
BASIC_CHORDS_.update(SUS_CHORDS)

def make_basic_chord(base, arrow_tokens):
    inflection = "".join(arrow_tokens)
    intervals, inflection_indices = BASIC_CHORDS_[base]
    chord = []
    for i, interval in enumerate(intervals):
        if i in inflection_indices:
            chord.append(interval + inflection)
        else:
            chord.append(interval)
    return chord


def expand_chord(token):
    if token in EXTRA_CHORDS:
        return EXTRA_CHORDS[token]

    added_tones = token.split("add")
    token = added_tones.pop(0)

    added_intervals = [accidental_to_quality(tone) for tone in added_tones]

    sus_replacement = None
    if "sus" in token:
        token, sus_token = token.split("sus")
        sus_replacement = accidental_to_quality(sus_token)

    prefix = ""
    if token.startswith("M") or token.startswith("d"):
        prefix = token[0]
        token = token[1:]
    separated = separate_by_arrows(token)
    base = prefix + separated.pop(0)

    chord = None

    if base in FLAVOR_CHORDS:
        chord = make_flavor_chord(base, separated)
    if base in BASIC_CHORDS:
        chord = make_basic_chord(base, separated)
    if sus_replacement is not None:
        if chord is None:
            raise ValueError("Sus replacement on an incompatible chord")
        chord[1] = sus_replacement
    if base in SUS_CHORDS:
        chord = make_basic_chord(base, separated)

    if chord is None:
        raise ValueError("Unrecognized chord {}".format(base))

    return chord + added_intervals
