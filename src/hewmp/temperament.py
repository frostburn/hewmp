from numpy import array, dot, isclose, logical_or, zeros
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


def temper_subgroup(just_mapping, comma_list, constraints, subgroup, num_iterations=1000, step_size=0.1, metric=None):
    """
    Return a tempered version of just intonation where only the subgroup is affected

    The result is minimaxed if there are no constraints
    """
    comma_sizes = array([dot(just_mapping, comma) for comma in comma_list])
    constraint_sizes = array([dot(just_mapping, constraint) for constraint in constraints])

    subgroup_just_mapping = array([dot(basis_vector, just_mapping) for basis_vector in subgroup])
    normalized_subgroup = [basis_vector / abs(basis_vector).sum() for basis_vector in subgroup]

    # Pinkan kludge fix  # TODO: Figure out the correct math for the general case
    if normalized_subgroup:
        renorm = False
        for i in range(len(normalized_subgroup[0])):
            count = 0
            for base in normalized_subgroup:
                if base[i] != 0:
                    count += 1
            if count > 1:
                for base in normalized_subgroup:
                    base[i] = 0
                    renorm = True
        if renorm:
            normalized_subgroup = [basis_vector / abs(basis_vector).sum() for basis_vector in normalized_subgroup]


    comma_list = [array([dot(basis_vector, comma) for basis_vector in normalized_subgroup]) for comma in comma_list]
    constraints = [array([dot(basis_vector, constraint) for basis_vector in normalized_subgroup]) for constraint in constraints]
    if len(constraints) == 1:
        constraint = constraints.pop()
    else:
        constraint = None
    if metric is not None:
        metric = array([dot(abs(basis_vector), metric) for basis_vector in subgroup])

    if not isclose(array([dot(subgroup_just_mapping, comma) for comma in comma_list]), comma_sizes).all():
        raise ValueError("Non-orthogonal subgroup or comma outside subgroup")
    if not isclose(array([dot(subgroup_just_mapping, constraint) for constraint in constraints]), constraint_sizes).all():
        raise ValueError("Non-orthogonal subgroup or constraint outside subgroup")

    subgroup_mapping = temper(subgroup_just_mapping, comma_list, constraints, num_iterations, step_size)
    if not constraints:
        if constraint is None:
            if metric is not None:
                subgroup_mapping = minimax(subgroup_just_mapping*metric, subgroup_mapping*metric) / metric
            else:
                subgroup_mapping = minimax(subgroup_just_mapping, subgroup_mapping)
        else:
            subgroup_mapping *= dot(subgroup_just_mapping, constraint) / dot(subgroup_mapping, constraint)


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


def comma_reduce(pitch, comma_list, persistence=5, cache=None):
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
    if cache is not None:
        cache_key = tuple(current)
        if cache_key in cache:
            return array(cache[cache_key])
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
    if cache is not None:
        cache[cache_key] = array(best)
    return best


def comma_root(pitch, degree, comma_list, persistence=5, cache=None):
    """
    Find the nth degree root of a pitch using commas from the list.
    Has the same frequency as the nth fraction of the pitch, but with integral representation.

    Returns None if the root couldn't be found.
    """
    cache_key = (tuple(pitch), degree)
    if cache is not None and cache_key in cache:
        return cache[cache_key]
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
    if cache is not None:
        if best is not None:
            cache[cache_key] = array(best)
        else:
            cache[cache_key] = None
    return best


def comma_equals(pitch_a, pitch_b, comma_list, persistence=5, cache=None):
    return (comma_reduce(pitch_a - pitch_b, comma_list, persistence=persistence, cache=cache) == 0).all()


def infer_subgroup(comma_list):
    if not comma_list:
        return []
    result = []
    used = array([False] * len(comma_list[0]))
    for comma in comma_list:
        used = logical_or(used, comma != 0)
    for i, in_use in enumerate(used):
        if in_use:
            basis_vector = zeros(len(used))
            basis_vector[i] = 1
            result.append(basis_vector)
    return result


if __name__ == "__main__":
    import argparse
    from numpy import log, exp
    from .monzo import fraction_to_monzo, PRIMES
    from .event import DEFAULT_METRIC
    from .temperaments import TEMPERAMENTS

    parser = argparse.ArgumentParser(description='Display the mapping for the given comma list')
    parser.add_argument('commas', nargs="+", type=str)
    parser.add_argument('--constraints', nargs="*", type=str)
    parser.add_argument('--subgroup', type=str)
    args = parser.parse_args()

    if args.commas[0] in TEMPERAMENTS:
        commas, subgroup = TEMPERAMENTS[args.commas[0]]
        print(commas, subgroup)
    else:
        commas, subgroup = args.commas, args.subgroup


    comma_list = []
    for comma in commas:
        monzo, unrepresentable = fraction_to_monzo(comma)
        if unrepresentable != 1:
            raise ValueError("Comma beyond supported {} limit".format(PRIMES[-1]))
        comma_list.append(monzo)
    if subgroup:
        basis_vectors = []
        for basis in subgroup.split("."):
            monzo, unrepresentable = fraction_to_monzo(basis)
            if unrepresentable != 1:
                raise ValueError("Subgroup beyond supported {} limit".format(PRIMES[-1]))
            basis_vectors.append(monzo)
    else:
        basis_vectors = infer_subgroup(comma_list)
    constraints = []
    for constraint in args.constraints or []:
        monzo, unrepresentable = fraction_to_monzo(constraint)
        if unrepresentable != 1:
            raise ValueError("Constraint beyond supported {} limit".format(PRIMES[-1]))
        constraints.append(monzo)

    JI = log(array(PRIMES))

    mapping = temper_subgroup(JI, comma_list, constraints, basis_vectors, metric=DEFAULT_METRIC)

    for m, p in zip(mapping, PRIMES):
        if not isclose(m, log(p)):
            print(m/log(2)*1200)

    for m, p in zip(mapping, PRIMES):
        error = (m-log(p))/log(2)*1200
        if not isclose(error, 0):
            if error >= 0:
                error = "+" + str(error)
            else:
                error = str(error)
            print(p, "->", exp(m), "~", error)
