import argparse
from collections import Counter, defaultdict
from numpy import around, log, array, dot
from hewmp.temperaments import TEMPERAMENTS
from hewmp.parser import PRIMES, IntervalParser


JI = log(array(PRIMES))


def warts_to_val(wart_str, index=0):
    token, divided_token = wart_str.lower().rsplit("d", 1)
    if divided_token == "o":
        edn_divided = 2
    elif divided_token == "t":
        edn_divided = 3
    elif divided_token == "p":
        edn_divided = 5
    else:
        edn_divided = int(divided_token)
    token = token[:-1]
    warts = Counter()
    while token[-1].isalpha():
        wart = token[-1].lower()
        warts[ord(wart) - ord("a")] += 1
        token = token[:-1]
    edn_divisions = int(token)
    generator = log(edn_divided) / edn_divisions
    steps = around(JI/generator)
    mapping = steps*generator
    for index, count in warts.items():
        modification = ((count + 1)//2) * (2*(count%2) - 1)
        if mapping[index] > JI[index]:
            steps[index] -= modification
        else:
            steps[index] += modification
    return steps.astype(int), edn_divided


def update_list_dict(target, source):
    for key, value in source.items():
        target[key].extend(value)


def hewmp_spellings(interval_parser, steps, edn_divided, preferred_arrows):
    spellings = defaultdict(list)
    for value in range(1, 9):
        if value in (1, 4, 5, 8):
            qualities = "P"
        else:
            qualities = "mM"
        for quality in qualities:
            token = "{}{}".format(quality, value)
            pitch = interval_parser.parse(token)[0]
            index = int(dot(steps, pitch[:len(steps)]))
            spellings[index].append(token)
    for value in range(1, 9):
        for quality in "dA":
            token = "{}{}".format(quality, value)
            pitch = interval_parser.parse(token)[0]
            index = int(dot(steps, pitch[:len(steps)]))
            spellings[index].append(token)

    required = set(range(steps[PRIMES.index(edn_divided)]))
    spelled = set(spellings.keys())
    missing = required - spelled
    if missing:
        new_spellings = defaultdict(list)
        for value in range(1, 9):
            for quality in ("dd", "AA"):
                token = "{}{}".format(quality, value)
                pitch = interval_parser.parse(token)[0]
                index = int(dot(steps, pitch[:len(steps)]))
                new_spellings[index].append(token)
        still_missing = required - spelled - set(new_spellings.keys())
        if len(still_missing) < len(missing):
            update_list_dict(spellings, new_spellings)
        spelled = set(spellings.keys())
        missing = required - spelled
        arrow_pairs = ["-+", "<>", "^v", "i!", "*%", "AV", "ud", "UD", "MW"]
        if preferred_arrows:
            arrow_pairs.insert(0, preferred_arrows)
        while missing and arrow_pairs:
            pair = arrow_pairs.pop(0)
            new_spellings = defaultdict(list)
            for value in range(1, 9):
                if value in (1, 4, 5, 8):
                    qualities = "P"
                else:
                    qualities = "mM"
                for quality in qualities:
                    for arrow in pair:
                        token = "{}{}{}".format(quality, value, arrow)
                        pitch = interval_parser.parse(token)[0]
                        index = int(dot(steps, pitch[:len(steps)]))
                        new_spellings[index].append(token)
            for value in range(1, 9):
                for quality in "dA":
                    for arrow in pair:
                        token = "{}{}{}".format(quality, value, arrow)
                        pitch = interval_parser.parse(token)[0]
                        index = int(dot(steps, pitch[:len(steps)]))
                        new_spellings[index].append(token)
            still_missing = required - spelled - set(new_spellings.keys())
            if len(still_missing) < len(missing):
                update_list_dict(spellings, new_spellings)
            spelled = set(spellings.keys())
            missing = required - spelled
    return spellings, missing


def hewmp_pitch_spellings(interval_parser, steps, edn_divided, preferred_arrows):
    spellings = defaultdict(list)
    bases = []
    for letter in "CDEFGaBc":
        octave = 4
        if letter == "c":
            letter = "C"
            octave = 5
        bases.append("{}{}".format(letter, octave))
    for token in bases:
        pitch = interval_parser.parse(token)[0]
        index = int(dot(steps, pitch[:len(steps)]))
        spellings[index].append(token)
    for base in bases:
        for accidental in "#b":
            token = "{}{}".format(base, accidental)
            pitch = interval_parser.parse(token)[0]
            index = int(dot(steps, pitch[:len(steps)]))
            spellings[index].append(token)

    required = set(range(steps[PRIMES.index(edn_divided)]))
    spelled = set(spellings.keys())
    missing = required - spelled
    if missing:
        new_spellings = defaultdict(list)
        for base in bases:
            for accidental in ("x", "bb"):
                token = "{}{}".format(base, accidental)
                pitch = interval_parser.parse(token)[0]
                index = int(dot(steps, pitch[:len(steps)]))
                new_spellings[index].append(token)
        still_missing = required - spelled - set(new_spellings.keys())
        if len(still_missing) < len(missing):
            update_list_dict(spellings, new_spellings)
        spelled = set(spellings.keys())
        missing = required - spelled
        arrow_pairs = ["-+", "<>", "^v", "i!", "*%", "AV", "ud", "UD", "MW"]
        if preferred_arrows:
            arrow_pairs.insert(0, preferred_arrows)
        while missing and arrow_pairs:
            pair = arrow_pairs.pop(0)
            new_spellings = defaultdict(list)
            for base in bases:
                for arrow in pair:
                    token = "{}{}".format(base, arrow)
                    pitch = interval_parser.parse(token)[0]
                    index = int(dot(steps, pitch[:len(steps)]))
                    new_spellings[index].append(token)
            for base in bases:
                for accidental in "#b":
                    for arrow in pair:
                        token = "{}{}{}".format(base, accidental, arrow)
                        pitch = interval_parser.parse(token)[0]
                        index = int(dot(steps, pitch[:len(steps)]))
                        new_spellings[index].append(token)
            still_missing = required - spelled - set(new_spellings.keys())
            if len(still_missing) < len(missing):
                update_list_dict(spellings, new_spellings)
            spelled = set(spellings.keys())
            missing = required - spelled
    return spellings, missing


def smitonic_spellings(interval_parser, steps, edn_divided, preferred_arrows):
    spellings = defaultdict(list)
    for value in range(1, 9):
        if value in (1, 3, 6, 8):
            qualities = "p"
        else:
            qualities = "sL"
        for quality in qualities:
            token = "{}{}".format(quality, value)
            pitch = interval_parser.parse(token)[0]
            index = dot(steps, pitch[:len(steps)])
            if index == int(index):
                spellings[int(index)].append(token)
    for value in range(1, 9):
        for quality in "nW":
            token = "{}{}".format(quality, value)
            pitch = interval_parser.parse(token)[0]
            index = dot(steps, pitch[:len(steps)])
            if index == int(index):
                spellings[int(index)].append(token)

    required = set(range(steps[PRIMES.index(edn_divided)]))
    spelled = set(spellings.keys())
    missing = required - spelled
    if missing:
        new_spellings = defaultdict(list)
        for value in range(1, 9):
            for quality in ("nn", "WW"):
                token = "{}{}".format(quality, value)
                pitch = interval_parser.parse(token)[0]
                index = dot(steps, pitch[:len(steps)])
                if index == int(index):
                    new_spellings[int(index)].append(token)
        still_missing = required - spelled - set(new_spellings.keys())
        if len(still_missing) < len(missing):
            update_list_dict(spellings, new_spellings)
        spelled = set(spellings.keys())
        missing = required - spelled
        arrow_pairs = ["<>", "^v", "-+", "i!", "*%", "AV", "ud", "UD", "MW"]
        if preferred_arrows:
            arrow_pairs.insert(0, preferred_arrows)
        while missing and arrow_pairs:
            pair = arrow_pairs.pop(0)
            new_spellings = defaultdict(list)
            for value in range(1, 9):
                if value in (1, 3, 6, 8):
                    qualities = "p"
                else:
                    qualities = "sL"
                for quality in qualities:
                    for arrow in pair:
                        token = "{}{}{}".format(quality, value, arrow)
                        pitch = interval_parser.parse(token)[0]
                        index = dot(steps, pitch[:len(steps)])
                        if index == int(index):
                            new_spellings[int(index)].append(token)
            for value in range(1, 9):
                for quality in "nW":
                    for arrow in pair:
                        token = "{}{}{}".format(quality, value, arrow)
                        pitch = interval_parser.parse(token)[0]
                        index = dot(steps, pitch[:len(steps)])
                        if index == int(index):
                            new_spellings[int(index)].append(token)
            still_missing = required - spelled - set(new_spellings.keys())
            if len(still_missing) < len(missing):
                update_list_dict(spellings, new_spellings)
            spelled = set(spellings.keys())
            missing = required - spelled
    return spellings, missing


def smitonic_pitch_spellings(interval_parser, steps, edn_divided, preferred_arrows):
    spellings = defaultdict(list)
    bases = []
    for letter in "JKNOQRSj":
        octave = 4
        if letter == "j":
            letter = "J"
            octave = 5
        bases.append("{}{}".format(letter, octave))
    for token in bases:
        pitch = interval_parser.parse(token)[0]
        index = dot(steps, pitch[:len(steps)])
        if index == int(index):
            spellings[int(index)].append(token)
    for base in bases:
        for accidental in "#b":
            token = "{}{}".format(base, accidental)
            pitch = interval_parser.parse(token)[0]
            index = dot(steps, pitch[:len(steps)])
            if index == int(index):
                spellings[int(index)].append(token)

    required = set(range(steps[PRIMES.index(edn_divided)]))
    spelled = set(spellings.keys())
    missing = required - spelled
    if missing:
        new_spellings = defaultdict(list)
        for base in bases:
            for accidental in ("x", "bb"):
                token = "{}{}".format(base, accidental)
                pitch = interval_parser.parse(token)[0]
                index = dot(steps, pitch[:len(steps)])
                if index == int(index):
                    new_spellings[int(index)].append(token)
        still_missing = required - spelled - set(new_spellings.keys())
        if len(still_missing) < len(missing):
            update_list_dict(spellings, new_spellings)
        spelled = set(spellings.keys())
        missing = required - spelled
        arrow_pairs = ["<>", "^v", "-+", "i!", "*%", "AV", "ud", "UD", "MW"]
        if preferred_arrows:
            arrow_pairs.insert(0, preferred_arrows)
        while missing and arrow_pairs:
            pair = arrow_pairs.pop(0)
            new_spellings = defaultdict(list)
            for base in bases:
                for arrow in pair:
                    token = "{}{}".format(base, arrow)
                    pitch = interval_parser.parse(token)[0]
                    index = dot(steps, pitch[:len(steps)])
                    if index == int(index):
                        new_spellings[int(index)].append(token)
            for base in bases:
                for accidental in "#b":
                    for arrow in pair:
                        token = "{}{}{}".format(base, accidental, arrow)
                        pitch = interval_parser.parse(token)[0]
                        index = dot(steps, pitch[:len(steps)])
                        if index == int(index):
                            new_spellings[int(index)].append(token)
            still_missing = required - spelled - set(new_spellings.keys())
            if len(still_missing) < len(missing):
                update_list_dict(spellings, new_spellings)
            spelled = set(spellings.keys())
            missing = required - spelled
    return spellings, missing


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Suggest HEWMP notation for the given tuning')
    parser.add_argument('tuning', type=str)
    parser.add_argument('--smitonic', action="store_true")
    parser.add_argument('--arrows', type=str)
    args = parser.parse_args()

    interval_parser = IntervalParser()
    interval_parser.set_base_pitch("C4")
    interval_parser.set_base_pitch("J4")

    steps, edn_divided = warts_to_val(args.tuning)
    print("Val", steps)

    print("Inflections:")
    if args.smitonic:
        for unison in ["n1", "p1-", "p1D", "p1W", "p1v", "p1!", "p1V", "p1d", "p1%", "p1<", "p1>", "p1*", "p1u", "p1A", "p1i", "p1^", "p1M", "p1U", "p1+", "W1"]:
            pitch = interval_parser.parse(unison)[0]
            width = dot(steps, pitch[:len(steps)])
            if width == int(width):
                width = int(width)
            print(unison, "=", width)
        spellings, missing = smitonic_spellings(interval_parser, steps, edn_divided, args.arrows)
        pitch_spellings, _ = smitonic_pitch_spellings(interval_parser, steps, edn_divided, args.arrows)
    else:
        for unison in ["d1", "P1W", "P1v", "P1D", "P1<", "P1!", "P1-", "P1d", "P1%", "P1V", "P1A", "P1*", "P1u", "P1+", "P1i", "P1>", "P1U", "P1^", "P1M", "A1"]:
            pitch = interval_parser.parse(unison)[0]
            print(unison, "=", int(dot(steps, pitch[:len(steps)])))
        spellings, missing = hewmp_spellings(interval_parser, steps, edn_divided, args.arrows)
        pitch_spellings, _ = hewmp_pitch_spellings(interval_parser, steps, edn_divided, args.arrows)

    print()
    print("Spellings:")
    for num in sorted(spellings.keys()):
        if num == 0:
            print("-" * 30)
        print("{}:{}".format(num, ",".join(spellings[num])))
        if num == steps[PRIMES.index(edn_divided)]:
            print("-" * 30)
    print()
    print("Pitch spellings:")
    for num in sorted(pitch_spellings.keys()):
        if num == 0:
            print("-" * 30)
        print("{}:{}".format(num, ",".join(pitch_spellings[num])))
        if num == steps[PRIMES.index(edn_divided)]:
            print("-" * 30)
    if missing:
        print("Failed to cover everything with the available arrows")
