# coding: utf-8

PERCUSSION_SHORTHANDS = {
    "k": (35, "Acoustic Bass Drum"),
    "K": (36, "Electric Bass Drum"),
    "st": (37, "Side Stick"),
    "z": (37, "Side Stick"),
    "s": (38, "Acoustic Snare"),
    "hc": (39, "Hand Clap"),
    "x": (39, "Hand Clap"),
    "S": (40, "Electric Snare"),
    "t0": (41, "Low Floor Tom"),
    "0": (41, "Low Floor Tom"),
    "h": (42, "Closed Hi-hat"),
    "t1": (43, "High Floor Tom"),
    "1": (43, "High Floor Tom"),
    "H": (44, "Pedal Hi-hat"),
    "t2": (45, "Low Tom"),
    "2": (45, "Low Tom"),
    "o": (46, "Open Hi-hat"),
    "t3": (47, "Low-Mid Tom"),
    "3": (47, "Low-Mid Tom"),
    "t4": (48, "Hi-Mid Tom"),
    "4": (48, "Hi-Mid Tom"),
    "c": (49, "Crash Cymbal 1"),
    "t5": (50, "High Tom"),
    "5": (50, "High Tom"),
    "r": (51, "Ride Cymbal 1"),
    "cc": (52, "Chinese Cymbal"),
    "y": (52, "Chinese Cymbal"),
    "rb": (53, "Ride Bell"),
    "d": (53, "Ride Bell"),
    "tr": (54, "Tambourine"),
    "j": (54, "Tambourine"),
    "sc": (55, "Splash Cymbal"),
    "Y": (55, "Splash Cymbal"),
    "cb": (56, "Cowbell"),
    "e": (56, "Cowbell"),
    "C": (57, "Crash Cymbal 2"),
    "v": (58, "Vibraslap"),
    "R": (59, "Ride Cymbal 2"),
    "B": (60, "High Bongo"),
    "b": (61, "Low Bongo"),
    "m1": (62, "Mute High Conga"),
    "M": (62, "Mute High Conga"),
    "c1": (63, "Open High Conga"),
    "G": (63, "Open High Conga"),
    "c0": (64, "Low Conga"),
    "g": (64, "Low Conga"),
    "T1": (65, "High Timbale"),
    "I": (65, "High Timbale"),
    "T0": (66, "Low Timbale"),
    "i": (66, "Low Timbale"),
    "A": (67, "High Agogô"),
    "a": (68, "Low Agogô"),
    "Z": (69, "Cabasa"),
    "m": (70, "Maracas"),
    "sw": (71, "Short Whistle"),
    "l": (71, "Short Whistle"),
    "lw": (72, "Long Whistle"),
    "L": (72, "Long Whistle"),
    "sg": (73, "Short Guiro"),
    "q": (73, "Short Guiro"),
    "lg": (74, "Long Guiro"),
    "Q": (74, "Long Guiro"),
    "cs": (75, "Claves"),
    "X": (75, "Claves"),
    "W": (76, "High Woodblock"),
    "w": (77, "Low Woodblock"),
    "mc": (78, "Mute Cuica"),
    "u": (78, "Mute Cuica"),
    "oc": (79, "Open Cuica"),
    "U": (79, "Open Cuica"),
    "mt": (80, "Mute Triangle"),
    "n": (80, "Mute Triangle"),
    "ot": (81, "Open Triangle"),
    "N": (81, "Open Triangle"),
}


if __name__ == "__main__":
    by_index = {}
    for key, (index, _) in PERCUSSION_SHORTHANDS.items():
        if len(key) == 1:
            by_index[index] = key

    for i in range(35, 82):
        if i not in by_index:
            print(i, "missing")

    longs = []
    print("| shorthand | name | index |")
    print("|:---------:|:----:|:-----:|")
    for key, (index, name) in PERCUSSION_SHORTHANDS.items():
        if len(key) == 1:
            print("|", key, "|", name, "|", index, "|")
        else:
            longs.append((key, name, index))
    print()
    print("## Longer Forms")
    print("| shorthand | name | index |")
    print("|:---------:|:----:|:-----:|")
    for key, name, index in longs:
        print("|", key, "|", name, "|", index, "|")
