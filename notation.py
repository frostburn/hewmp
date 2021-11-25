"""
Tools for reversing parsed notation back into a standard form.
In other words in combination with parsing translate relative intervals like M3- to ratio notation such as 5/4 or (absolute) pitch notation like C5#-
"""
from numpy import array, log, pi, maximum


def notate_extras(pitch, e_index=None, hz_index=None, rad_index=None):
    """
    Notate extra bits like cents, Hz and phase offsets as transpositions
    """
    result = []
    if e_index is not None:
        nats = pitch[e_index]
        if nats != 0:
            result.append("{}c".format(nats*1200/log(2)))
    if hz_index is not None:
        hz = pitch[hz_index]
        if hz != 0:
            result.append("{}Hz".format(hz))
    if rad_index is not None:
        rads = pitch[rad_index]
        if rads != 0:
            result.append("{}deg".format(180*rads/pi))
    if result:
        return "&" + "&".join(result)
    return ""


def notate_fraction(pitch, primes, *extra_indices):
    """
    Notate pitch monzo defined by the primes as a fraction p/q
    """
    numerator = 1
    denominator = 1
    for coord, prime in zip(pitch, primes):
        if coord != int(coord):
            raise ValueError("Non-integral monzo")
        coord = int(coord)
        if coord > 0:
            numerator *= prime**coord
        if coord < 0:
            denominator *= prime**(-coord)
    if denominator == 1:
        return "{}{}".format(numerator, notate_extras(pitch, *extra_indices))
    return "{}/{}{}".format(numerator, denominator, notate_extras(pitch, *extra_indices))


def notate_otonal_utonal(pitches, primes):
    """
    Notate a chord like =M- in otonal (4:5:6) or utonal (15;12;10) notation depending on which one is simpler

    Assumes that there are no extra bits
    """
    if len(pitches) < 2:
        raise ValueError("Need at least two pitches to make a chord")
    otonal_root = -array(pitches[0])
    utonal_root = array(pitches[0])
    for pitch in pitches[1:]:
        otonal_root = maximum(otonal_root, -array(pitch))
        utonal_root = maximum(utonal_root, pitch)

    otonal = []
    utonal = []
    for pitch in pitches:
        num_otonal = 1
        num_utonal = 1
        for coord, prime, o, u in zip(pitch, primes, otonal_root, utonal_root):
            if coord != int(coord):
                raise ValueError("Non-integral monzo")
            num_otonal *= prime**int(coord + o)
            num_utonal *= prime**int(u - coord)
        otonal.append(num_otonal)
        utonal.append(num_utonal)

    if max(otonal) <= max(utonal):
        return ":".join(map(str, otonal))
    return ";".join(map(str, utonal))
