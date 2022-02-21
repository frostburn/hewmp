from fractions import Fraction
from numpy import array, zeros, log, exp, dot


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


class SemiMonzo:
    """
    Vector representation of a fraction or an nth root of a fraction
    """
    def __init__(self, value=None, residual=None, nats=None):
        if isinstance(value, Fraction):
            if residual is not None:
                raise ValueError("Residual already given when converting fraction to monzo")
            if value == 0:
                value = None
                residual = Fraction(0)
            else:
                value, residual = fraction_to_monzo(value)
        if residual is None:
            residual = Fraction(1)
        if nats is None:
            nats = 0.0
        if value is None:
            self.vector = array([Fraction(0)] * len(PRIMES))
        else:
            # Monzo components of nth roots of fractions up to 31-limit (logarithmic)
            self.vector = array([Fraction(component) for component in value])
        # Fraction beyond 31-limit (non-logarithmic)
        self.residual = residual
        # Logarithmic residual
        self.nats = nats

    @property
    def total_nats(self):
        if self.residual == 0:
            return float("-inf")
        return log(float(self.residual)) + self.nats

    def __neg__(self):
        return self.__class__(-self.vector, 1/self.residual, -self.nats)

    def __add__(self, other):
        """
        Add logarithms. Multiply fractions.
        """
        vector = self.vector + other.vector
        residual = self.residual * other.residual
        nats = self.nats + other.nats
        return self.__class__(vector, residual, nats)

    def __sub__(self, other):
        """
        Subtrac logarithms. Divide fractions.
        """
        vector = self.vector - other.vector
        residual = self.residual / other.residual
        nats = self.nats - other.nats
        return self.__class__(vector, residual, nats)

    def __mul__(self, other):
        """
        Raise to the nth power
        """
        if other == 1:
            return self.__class__(self.vector, self.residual, self.nats)
        other = Fraction(other)
        vector = [component * other for component in self.vector]
        if other.denominator == 1:
            residual = self.residual ** other
            nats = self.nats * other
        else:
            residual = None
            nats = self.total_nats * float(other)
        return self.__class__(vector, residual, nats)

    def __truediv__(self, other):
        """
        Take the nth root.
        """
        if other == 1:
            return self.__class__(self.vector, self.residual, self.nats)
        other = Fraction(other)
        vector = [component / other for component in self.vector]
        nats = self.total_nats / float(other)
        return self.__class__(vector, None, nats)

    def __eq__(self, other):
        return (self.vector == other.vector).all() and self.residual == other.residual and self.nats == other.nats

    def copy(self):
        return self.__class__(self.vector, self.residual, self.nats)

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.vector, self.residual, self.nats)

    def float_vector(self):
        return array([float(component) for component in self.vector])


def et_to_semimonzo(num_steps, et_divisions, et_divided):
    num_steps = Fraction(num_steps)
    et_divisions = Fraction(et_divisions)
    et_divided = Fraction(et_divided)
    result = SemiMonzo(et_divided)
    return result * num_steps / et_divisions


class Pitch:
    absolute = True
    def __init__(self, monzo=None, frequency_offset=0, phase=0):
        if monzo is None:
            monzo = SemiMonzo()
        elif not isinstance(monzo, SemiMonzo):
            monzo = SemiMonzo(monzo)
        self.monzo = monzo
        self.frequency_offset = frequency_offset
        self.phase = phase

    def copy(self):
        return self.__class__(self.monzo.copy(), self.frequency_offset, self.phase)

    def __eq__(self, other):
        if not isinstance(other, Pitch):
            return False
        return self.monzo == other.monzo and self.frequency_offset == other.frequency_offset and self.phase == other.phase

    def __sub__(self, other):
        monzo = self.monzo - other.monzo
        if isinstance(other, Pitch):
            frequency_delta = self.frequency_offset - other.frequency_offset
            phase_delta = self.phase - other.phase
            return Interval(monzo, frequency_delta, phase_delta)
        frequency_offset = self.frequency_offset - other.frequency_delta
        phase = self.phase - other.phase_delta
        return self.__class__(monzo, frequency_offset, phase)

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.monzo, self.frequency_offset, self.phase)


class Interval:
    absolute = False
    def __init__(self, monzo=None, frequency_delta=0, phase_delta=0):
        if monzo is None:
            monzo = SemiMonzo()
        elif not isinstance(monzo, SemiMonzo):
            monzo = SemiMonzo(monzo)
        self.monzo = monzo
        self.frequency_delta = frequency_delta
        self.phase_delta = phase_delta

    def __add__(self, other):
        monzo = self.monzo + other.monzo
        if isinstance(other, Pitch):
            frequency_offset = self.frequency_delta + other.frequency_offset
            phase = self.phase_delta + other.phase
            return other.__class__(monzo, frequency_offset, phase)
        frequency_delta = self.frequency_delta + other.frequency_delta
        phase_delta = self.phase_delta + other.phase_delta
        return self.__class__(monzo, frequency_delta, phase_delta)

    def __sub__(self, other):
        monzo = self.monzo - other.monzo
        frequency_delta = self.frequency_delta - other.frequency_delta
        phase_delta = self.phase_delta - other.phase_delta
        return self.__class__(monzo, frequency_delta, phase_delta)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        return self.__class__(self.monzo * other, self.frequency_delta * other, self.phase_delta * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return self.__class__(self.monzo / other, self.frequency_delta / other, self.phase_delta / other)

    def __neg__(self):
        return self.__class__(-self.monzo, -self.frequency_delta, -self.phase_delta)

    def copy(self):
        return self.__class__(self.monzo.copy(), self.frequency_delta, self.phase_delta)


class Mapping:
    def __init__(self, vector, base_frequency):
        self.vector = vector
        self.base_frequency = base_frequency

    def __call__(self, pitch):
        if not isinstance(pitch, Pitch):
            raise TypeError("Only pitches can be mapped to frequency")
        nats = dot(self.vector, pitch.monzo.vector) + pitch.monzo.total_nats
        return self.base_frequency * exp(nats) + pitch.frequency_offset
