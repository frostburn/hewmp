# coding: utf-8

# Wa = 3-limit = 2.3 subgroup
WA_CHORDS = {
    "6": ["P1", "M3", "P5", "M6"],  # Same as Madd6
    "6no3": ["P1", "P5", "M6"],
    "b6no3": ["P1", "P5", "m6"],
}

# Ya = 5-limit = 2.3.5 subgroup
YA_CHORDS = {
    "6-no3": ["P1", "P5", "M6-"],

    "b6+no3": ["P1", "P5", "m6+"],

    "o": ["P1", "m3+", "d5+2"],
    "dim": ["P1", "m3+", "d5+2"],
    "dim7": ["P1", "m3+", "d5+2", "d7+3"],
    "o10": ["P1", "m3+", "d5+2", "M10"],
    "o10-": ["P1", "m3+", "d5+2", "M10-"],
    "dim10": ["P1", "m3+", "d5+2", "M10"],
    "dim10-": ["P1", "m3+", "d5+2", "M10-"],
    "o11": ["P1", "m3+", "d5+2", "P11"],
    "o11+": ["P1", "m3+", "d5+2", "P11+"],
    "dim11": ["P1", "m3+", "d5+2", "P11"],
    "dim11+": ["P1", "m3+", "d5+2", "P11+"],

    "aug": ["P1", "M3-", "A5-2"],
    "augb10": ["P1", "M3-", "A5-2", "m10"],
    "augb10+": ["P1", "M3-", "A5-2", "m10+"],

    "ø":     ["P1", "m3+", "d5+2", "m7+"],
    "hdim":  ["P1", "m3+", "d5+2", "m7+"],
    "ø7":    ["P1", "m3+", "d5+2", "m7+"],
    "hdim7": ["P1", "m3+", "d5+2", "m7+"],

    "hdom":  ["P1", "m3+", "d5+2", "m7"],

    "aug7-": ["P1", "M3-", "A5-2", "m7+"],
    "augdom": ["P1", "M3", "A5-2", "m7"],
    "augdom-": ["P1", "M3-", "A5-2", "m7"],

    "M7-aug": ["P1", "M3-", "A5-2", "M7-"],

    "M7-aug6add2": ["P1", "M2", "M3-", "P5", "A5-2", "M6", "M7-"],
    "M7-aug6add2#4-": ["P1", "M2", "M3-", "A4-", "P5", "A5-2", "M6", "M7-"],

    "m7b5": ["P1", "m3+", "d5+2", "m7+"],

    "6-": ["P1", "M3-", "P5", "M6"],  # Same as M-add6
    "6--": ["P1", "M3-", "P5", "M6-"],  # Same as M-add6-
    "6-/9": ["P1", "M3-", "P5", "M6", "M9"],  # Same as M-add6add9
    "6--/9": ["P1", "M3-", "P5", "M6-", "M9"],  # Same as M-add6-add9
    "6-/9-": ["P1", "M3-", "P5", "M6", "M9-"], # Same as M-add6add9-
    "6--/9-": ["P1", "M3-", "P5", "M6-", "M9-"], # Same as M-add6-add9-

    "m+6": ["P1", "m3+", "P5", "M6"],  # Same as m+add6
    "m+6-": ["P1", "m3+", "P5", "M6-"],  # Same as m+add6-
    "m+6/9": ["P1", "m3+", "P5", "M6", "M9"],  # Same as m+add6add9
    "m+6-/9": ["P1", "m3+", "P5", "M6-", "M9"],  # Same as m+add6-add9
    "m+6/9-": ["P1", "m3+", "P5", "M6", "M9-"],  # Same as m+add6add9-
    "m+6-/9-": ["P1", "m3+", "P5", "M6-", "M9-"],  # Same as m+add6-add9-

    "M9--": ["P1", "M3-", "P5", "M7-", "M9-"],
    "M9--no5": ["P1", "M3-", "M7-", "M9-"],

    "m9++": ["P1", "m3+", "P5", "m7+", "M9+"],
    "m9++no5": ["P1", "m3+", "m7+", "M9+"],

    "9--": ["P1", "M3-", "P5", "m7+", "M9-"],
    "dom9--": ["P1", "M3-", "P5", "m7", "M9-"],

    "m+b6+addb9+": ["P1", "m3+", "P5", "m6+", "m7+", "m9+"],

    "M-b10+": ["P1", "M3-", "P5", "M7-", "m10+"],  # Same as M-addb10+
    "M-b10+no5": ["P1", "M3-", "M7-", "m10+"],

    "m+10-": ["P1", "m3+", "P5", "m7+", "M10-"],  # Same as m+add10-
    "m+10-no5": ["P1", "m3+", "M10-", "m7+", "M10-"],

    "7-b10+": ["P1", "M3-", "P5", "m7+", "m10+"],  # Same as 7-addb10+
    "7-b10+no5": ["P1", "M3-", "m7+", "m10+"],
    "dom-b10": ["P1", "M3-", "P5", "m7", "m10"],  # Same as dom-addb10
    "dom-b10+": ["P1", "M3-", "P5", "m7", "m10+"],  # Same as dom-addb10+

    "7-b9": ["P1", "M3-", "P5", "m7+", "m9"],  # Same as 7-addb9
    "7-b9+": ["P1", "M3-", "P5", "m7+", "m9+"],  # Same as 7-addb9+
    "7-b9+2": ["P1", "M3-", "P5", "m7+", "m9+2"],  # Same as 7-addb9+2
    "dom-b9+": ["P1", "M3-", "P5", "m7", "m9+"],  # Same as dom-addb9+

    "11-+": ["P1", "M3-", "P5", "m7+", "M9", "P11+"],
    "dom11-+": ["P1", "M3-", "P5", "m7", "M9", "P11+"],
    "dom9--11+": ["P1", "M3-", "P5", "m7", "M9-", "P11+"],

    "#11--": ["P1", "M3-", "P5", "m7+", "M9", "A11-"],
    "b12-+2": ["P1", "M3-", "P5", "m7+", "M9", "d12+2"],
    "domb12-+": ["P1", "M3-", "P5", "m7", "M9", "d12+"],
    "dom9--b12+": ["P1", "M3-", "P5", "m7", "M9-", "d12+"],

    "13--": ["P1", "M3-", "P5", "m7+", "M9", "M13-"],

    "dom13--": ["P1", "M3-", "P5", "m7", "M9", "M13-"],
    "dom9--13": ["P1", "M3-", "P5", "m7", "M9-", "M13"],
    "dom9--13-": ["P1", "M3-", "P5", "m7", "M9-", "M13-"],
}

OTONAL_CHORDS = {
    "h7": ["4/4", "5/4", "6/4", "7/4"],
    "h8f": ["4/4", "5/4", "6/4", "7/4", "8/4"],
    "h9": ["4/4", "5/4", "6/4", "7/4", "9/4"],
    "h9f": ["4/4", "5/4", "6/4", "7/4", "8/4", "9/4"],
    "h10f": ["4/4", "5/4", "6/4", "7/4", "8/4", "9/4", "10/4"],
    "h11": ["4/4", "5/4", "6/4", "7/4", "9/4", "11/4"],
    "h11f": ["4/4", "5/4", "6/4", "7/4", "8/4", "9/4", "10/4", "11/4"],
    "h12f": ["4/4", "5/4", "6/4", "7/4", "8/4", "9/4", "10/4", "11/4", "12/4"],
    "h13": ["4/4", "5/4", "6/4", "7/4", "9/4", "11/4", "13/4"],
    "h13f": ["4/4", "5/4", "6/4", "7/4", "8/4", "9/4", "10/4", "11/4", "12/4", "13/4"],
    "h14f": ["4/4", "5/4", "6/4", "7/4", "8/4", "9/4", "10/4", "11/4", "12/4", "13/4", "14/4"],
    "h15f": ["4/4", "5/4", "6/4", "7/4", "8/4", "9/4", "10/4", "11/4", "12/4", "13/4", "14/4", "15/4"],
    "h17": ["4/4", "5/4", "6/4", "7/4", "9/4", "11/4", "13/4", "17/4"],
    "h19": ["4/4", "5/4", "6/4", "7/4", "9/4", "11/4", "13/4", "17/4", "19/4"],
    "h23": ["4/4", "5/4", "6/4", "7/4", "9/4", "11/4", "13/4", "17/4", "19/4", "23/4"],
    "h29": ["4/4", "5/4", "6/4", "7/4", "9/4", "11/4", "13/4", "17/4", "19/4", "23/4", "29/4"],

    "dm5": ["5/5", "6/5", "7/5"],
    "dm6": ["5/5", "6/5", "7/5", "8/5"],
    "dm7": ["5/5", "6/5", "7/5", "8/5", "9/5"],
    "dm8f": ["5/5", "6/5", "7/5", "8/5", "9/5", "10/5"],
    "dm9": ["5/5", "6/5", "7/5", "8/5", "9/5", "11/5"],
    "dm9f": ["5/5", "6/5", "7/5", "8/5", "9/5", "10/5", "11/5"],
    "dm10": ["5/5", "6/5", "7/5", "8/5", "9/5", "11/5", "13/5"],
    "dm10f": ["5/5", "6/5", "7/5", "8/5", "9/5", "10/5", "11/5", "12/5", "13/5"],
    "dm13": ["5/5", "6/5", "7/5", "8/5", "9/5", "11/5", "13/5", "17/5"],
    "dm14": ["5/5", "6/5", "7/5", "8/5", "9/5", "11/5", "13/5", "17/5", "19/5"],

    "su4": ["6/6", "7/6", "8/6"],
    "su5": ["6/6", "7/6", "8/6", "9/6"],
    "su6": ["6/6", "7/6", "8/6", "9/6", "10/6"],
    "su7": ["6/6", "7/6", "8/6", "9/6", "10/6", "11/6"],
    "su8f": ["6/6", "7/6", "8/6", "9/6", "10/6", "11/6", "12/6"],
    "su9": ["6/6", "7/6", "8/6", "9/6", "10/6", "11/6", "13/6"],
    "su9f": ["6/6", "7/6", "8/6", "9/6", "10/6", "11/6", "12/6", "13/6"],

    "sud3": ["7/7", "8/7", "9/7"],
    "sud4": ["7/7", "8/7", "9/7", "10/7"],
    "sud5": ["7/7", "8/7", "9/7", "10/7", "11/7"],
    "sud6": ["7/7", "8/7", "9/7", "10/7", "11/7", "12/7"],
    "sud7": ["7/7", "8/7", "9/7", "10/7", "11/7", "12/7", "13/7"],
    "sud8f": ["7/7", "8/7", "9/7", "10/7", "11/7", "12/7", "13/7", "14/7"],
    "sud9": ["7/7", "8/7", "9/7", "10/7", "11/7", "12/7", "13/7", "15/7"],
    "sud9f": ["7/7", "8/7", "9/7", "10/7", "11/7", "12/7", "13/7", "14/7", "15/7"],

    "msu3": ["8/8", "8/9", "10/8"],
    "msu4": ["8/8", "8/9", "10/8", "11/8"],
    "msu5": ["8/8", "8/9", "10/8", "11/8", "12/8"],
    "msu6": ["8/8", "8/9", "10/8", "11/8", "12/8", "13/8"],

    "haug": ["8/8", "11/8", "13/8"],
    "haug8": ["8/8", "11/8", "13/8", "17/8"],

    "dmaug": ["9/9", "11/9", "13/9"],
    "dmaug8": ["9/9", "11/9", "13/9", "17/9"],

    "barb": ["10/10", "13/10", "15/10"],  # Same as Mi+
    "pinkan": ["10/10", "13/10", "15/10", "19/10"],  # Same as Mi+addb8+A
}

UTONAL_CHORDS = {
    "u5": ["7/7", "7/6", "7/5"],
    "u6": ["8/8", "8/7", "8/6", "8/5"],
    "us": ["9/9", "9/8", "9/7", "9/6"],
    "ug6": ["10/10", "10/9", "10/8", "10/7", "10/6"],
    "ug5": ["11/11", "11/9", "11/7"],
    "ug7": ["13/13", "13/11", "13/9", "13/7"],

    "mbarb": ["15/15", "15/13", "15/10"],  #  Same as m!-
    "mpinkan": ["19/19", "19/15", "19/13", "19/10"],
}

EXTRA_CHORDS = {
    "isl": ["1/1", "15/13", "4/3"],
    "isla": ["52/52", "52/45", "52/39"],  # Tempers to "isl" in Barbados
    "barb6": ["1/1", "13/10", "3/2", "26/15"],  # Same as Mi+add6i+
    "barbb6": ["1/1", "13/10", "3/2", "8/5"],  # Same as Mi+addb6+
    "barb7": ["1/1", "13/10", "3/2", "9/5"],  # Same as Mi+addb7+
}

EXTRA_CHORDS.update(WA_CHORDS)
EXTRA_CHORDS.update(YA_CHORDS)
EXTRA_CHORDS.update(OTONAL_CHORDS)
EXTRA_CHORDS.update(UTONAL_CHORDS)
