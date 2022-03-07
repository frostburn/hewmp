from numpy import array, dot, isclose, log
from hewmp.temperament import temper, temper_subgroup, comma_reduce, comma_root, minimax


if __name__ == '__main__':
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
