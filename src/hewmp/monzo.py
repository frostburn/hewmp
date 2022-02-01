from fractions import Fraction
from numpy import zeros


PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31)


def number_to_monzo(number):
    if number < 1:
        raise ValueError("Non-vectorizable number {}".format(number))
    pitch = zeros(len(PRIMES), int)
    for i, p in enumerate(PRIMES):
        while number % p == 0:
            number //= p
            pitch[i] += 1
    return pitch, number


def fraction_to_monzo(fraction):
    fraction = Fraction(fraction)
    positive_monzo, numerator = number_to_monzo(fraction.numerator)
    negative_monzo, denominator = number_to_monzo(fraction.denominator)
    return positive_monzo - negative_monzo, Fraction(numerator, denominator)
