from numpy import array, dot, isclose
from numpy.linalg import norm


def temper(just_mapping, comma_list, constraints, num_iterations=1000, step_size=0.5):
    """
    Temper out a given list of commas while keeping the constrained intervals pure if possible.

    The magnitude of the resulting mapping is arbitrary, but reasonably close to just intonation
    """
    j_factors = [dot(constraint, just_mapping) for constraint in constraints]

    mapping = array(just_mapping)

    normalized_comma_list = [comma / norm(comma) for comma in comma_list]
    for _ in range(num_iterations):
        for comma in normalized_comma_list:
            mapping -= dot(mapping, comma) * comma
        for constraint, j_factor in zip(constraints, j_factors):
            m_factor = dot(constraint, mapping)
            mapping -= constraint * (m_factor - j_factor) * m_factor * step_size
    return mapping


def minimax(just_mapping, mapping):
    """
    Scale the mapping to minimize the maximum error from just intonation.
    """
    least_error = float("inf")
    best_mapping = mapping
    for i in range(len(just_mapping)):
        for j in range(i+1, len(just_mapping)):
            candidate = mapping / (mapping[i] + mapping[j]) * (just_mapping[i] + just_mapping[j])
            error = abs(just_mapping - candidate).max()
            if error < least_error:
                least_error = error
                best_mapping = candidate
    return best_mapping


def temper_subgroup(just_mapping, comma_list, constraints, subgroup, num_iterations=1000, step_size=0.1):
    """
    Return a tempered version of just intonation where only the subgroup is affected

    The result is minimaxed if there are no constraints
    """
    comma_sizes = array([dot(just_mapping, comma) for comma in comma_list])
    constraint_sizes = array([dot(just_mapping, constraint) for constraint in constraints])

    subgroup_just_mapping = array([dot(basis_vector, just_mapping) for basis_vector in subgroup])
    normalized_subgroup = [basis_vector / abs(basis_vector).sum() for basis_vector in subgroup]
    comma_list = [array([dot(basis_vector, comma) for basis_vector in normalized_subgroup]) for comma in comma_list]
    constraints = [array([dot(basis_vector, constraint) for basis_vector in normalized_subgroup]) for constraint in constraints]

    if not isclose(array([dot(subgroup_just_mapping, comma) for comma in comma_list]), comma_sizes).all():
        raise ValueError("Non-orthogonal subgroup or comma outside subgroup")
    if not isclose(array([dot(subgroup_just_mapping, constraint) for constraint in constraints]), constraint_sizes).all():
        raise ValueError("Non-orthogonal subgroup or constraint outside subgroup")

    subgroup_mapping = temper(subgroup_just_mapping, comma_list, constraints, num_iterations, step_size)
    if not constraints:
        subgroup_mapping = minimax(subgroup_just_mapping, subgroup_mapping)

    mapping = array(just_mapping)
    for i, basis_vector in enumerate(subgroup):
        l1_normalizer = 1 / abs(basis_vector).sum()
        for j, coord in enumerate(basis_vector):
            mapping[j] += coord * (subgroup_mapping[i] - subgroup_just_mapping[i]) * l1_normalizer

    return mapping


def is_less_complex(pitch_a, pitch_b):
    """
    Compare pitches to see which one is expressed using smaller primes ignoring octaves
    """
    for i in reversed(range(1, len(pitch_a))):
        if abs(pitch_a[i]) < abs(pitch_b[i]):
            return True
        if abs(pitch_a[i]) > abs(pitch_b[i]):
            return False

    for i in reversed(range(1, len(pitch_a))):
        if pitch_a[i] > 0 and pitch_b[i] < 0:
            return True
        if pitch_a[i] < 0 and pitch_b[i] > 0:
            return False
    return False


def comma_reduce(pitch, comma_list, persistence=5):
    """
    Express the pitch using as small primes as possible by adding commas from the list
    """
    # Walk towards "zero"
    current = pitch
    did_advance = True
    while did_advance:
        did_advance = False
        for comma in comma_list:
            candidate = current + comma
            if is_less_complex(candidate, current):
                current = candidate
                did_advance = True
                continue
            candidate = current - comma
            if is_less_complex(candidate, current):
                current = candidate
                did_advance = True

    # Search the vicinity of "zero" for simpler options
    best = current
    def combine(coefs):
        nonlocal best
        if len(coefs) == len(comma_list):
            candidate = current + 0
            for coef, comma in zip(coefs, comma_list):
                candidate += coef*comma
            if is_less_complex(candidate, best):
                best = candidate
            return
        for i in range(-persistence, persistence+1):
            combine(coefs + [i])

    combine([])
    return best


def comma_root(pitch, degree, comma_list, persistence=5):
    """
    Find the nth degree root of a pitch using commas from the list.
    Has the same frequency as the nth fraction of the pitch, but with integral representation.

    Returns None if the root couldn't be found.
    """
    best = None
    def combine(coefs):
        nonlocal best
        if len(coefs) == len(comma_list):
            candidate = pitch + 0
            for coef, comma in zip(coefs, comma_list):
                candidate += coef*comma
            if (candidate % degree == 0).all():
                candidate //= degree
            else:
                return
            if best is None or is_less_complex(candidate, best):
                best = candidate
            return
        for i in range(-persistence, persistence+1):
            combine(coefs + [i])

    combine([])
    return best


if __name__ == "__main__":
    from numpy import log
    JI = log(array([2, 3, 5]))

    syntonic_comma = array([-4, 4, -1])
    meantone = temper(JI, [syntonic_comma], [])
    assert(isclose(dot(meantone, syntonic_comma), 0))

    quarter_comma_meantone = array([log(2), log(2) + log(5)/4, log(5)])
    octave = array([1, 0, 0])
    third = array([-2, 0, 1])
    candidate = temper(JI, [syntonic_comma], [octave, third])
    assert(isclose(candidate, quarter_comma_meantone).all())

    pythagorean_comma = array([-19, 12, 0])
    subgroup_2_3 = [array([1, 0, 0]), array([0, 1, 0])]
    compton = temper_subgroup(JI, [pythagorean_comma], [], subgroup_2_3)
    assert(isclose(dot(compton, pythagorean_comma), 0))
    assert(isclose(compton[2], JI[2]))
    error = compton-JI
    assert(isclose(error.max(), -error.min()))

    JI = log(array([2, 3, 5, 7, 11, 13]))
    island_comma = array([2, -3, -2, 0, 0, 2])
    island = minimax(JI, temper(JI, [island_comma], []))
    assert(isclose(dot(island, island_comma), 0))

    subgroup_2_3_13_per_15 = [array([1, 0, 0, 0, 0, 0]), array([0, 1, 0, 0, 0, 0]), array([0, 0, -1, 0, 0, 1])]
    barbados = temper_subgroup(JI, [island_comma], [], subgroup_2_3_13_per_15)
    assert(isclose(dot(barbados, island_comma), 0))

    assert (comma_reduce(array([1, -2, 1]), [syntonic_comma]) == array([-3, 2, 0])).all()

    assert (comma_root(array([0, 0, 1]), 4, [syntonic_comma]) == array([-1, 1, 0])).all()
