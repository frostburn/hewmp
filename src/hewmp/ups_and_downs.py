from fractions import Fraction


ARROW_INFLECTIONS = {
    # 2ED2 is a subset of 12
    # 3ED2 is a subset of 12
    # 4ED2 is a subset of 12
    "5ED2": (-3, 2),  # Whole step
    # 6ED2 is a subset of 12
    "7ED2": (-3, 2),
    # 8ED2 is a subset of 24
    "9ED2": (-3, 2),
    "10ED2": (-Fraction(3, 2), 1),  # Half of 5edo
    "11ED2": (-3, 2),
    "12ED2": (8, -5),  # Semitone
    "13bED2": (-3, 2),
    "14ED2": (-1.5, 1),  # Half of 7edo
    "15ED2": (-1, Fraction(2, 3)),  # Third of 5edo
    "16ED2": (11, -7),  # Negative augmented unison
    "17ED2": (8, -5),
    "18bED2": (-Fraction(3, 2), 1),  # Half of 9edo
    "19ED2": (-11, 7),  # Augmented unison
    "20ED2": (-Fraction(3, 4), 0.5),  # Quarter of 5edo
    "21ED2": (-1, Fraction(2, 3)),  # Third of 7edo
    "22ED2": (8, -5),
    "23ED2": (11, -7),
    "24ED2": (4, -Fraction(5, 2)),  # Quartertone (half semitone)
    "25ED2": (-Fraction(3, 5), Fraction(2, 5)),  # Fifth of 5edo
    "26ED2": (-11, 7),
    "27ED2": (8, -5),
    "28ED2": (-Fraction(3, 4), Fraction(1, 2)),  # Quarter of 7edo
    "29ED2": (4, -Fraction(5, 2)),
    "30ED2": (-0.5, Fraction(1, 3)),  # Sixth of 5edo
    "31ED2": (-Fraction(11, 2), Fraction(7, 2)),  # Half-augmented unison
    "32ED2": (8, -5),
    "33ED2": (-11, 7),
    "34ED2": (4, -Fraction(5, 2)),
    "35ED2": (-Fraction(3, 5), Fraction(2, 5)),  # Fifth of 7edo
    "35bED2": (-Fraction(3, 7), Fraction(2, 7)),  # Seventh of 5edo
    "36ED2": (Fraction(8, 3), -Fraction(5, 3)),  # Third of a semitone
    "37ED2": (8, -5),
    "38ED2": (-Fraction(11, 2), Fraction(7, 2)),
    "39ED2": (4, -Fraction(5, 2)),
    "40ED2": (-11, 7),
    "41ED2": (Fraction(8, 3), -Fraction(5, 3)),
}


if __name__ == "__main__":
    from numpy import dot
    from .tuning_notation import warts_to_val

    for wart_str, arrow in ARROW_INFLECTIONS.items():
        val, et_divided = warts_to_val(wart_str)
        steps = dot(val[:len(arrow)], arrow)
        F = dot(val[:2], [0, 0])
        D = dot(val[:2], [-5, 3])
        E = dot(val[:2], [-8, 5])
        F_sharp = dot(val[:2], [-11, 7])
        print(wart_str, steps)
        print("P5={}".format(val[1]-val[0]))
        print("D={} E={} F={} F#={}".format(D-D, E-D, F-D, F_sharp-D))
        print()
