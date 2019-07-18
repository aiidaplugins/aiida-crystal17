from ase.spacegroup import crystal
import numpy as np
import pytest
import six

from aiida_crystal17.symmetry import (
    prepare_for_spglib, compute_symmetry_dataset, standardize_cell, find_primitive,
    operations_cart_to_frac, operations_frac_to_cart, get_hall_number_from_symmetry,
    structure_info, reset_kind_names)


def test_struct_info(db_test_app, get_structure):
    string = structure_info(get_structure("MgO"))
    assert isinstance(string, six.string_types)


def test_reset_kind_names(db_test_app, get_structure):
    struct = get_structure("NiO_afm")
    names = ["Ni_u", "Ni_u", "Ni_d", "Ni_d", "O", "O", "O", "O"]
    new_struct = reset_kind_names(struct, names)
    assert [s.kind_name for s in new_struct.sites] == names


def test_reset_kind_names_fail(db_test_app, get_structure):
    struct = get_structure("NiO_afm")
    names = ["Ni_u", "Ni_u", "Ni_d", "Ni_d", "Ni_d", "O", "O", "O"]
    with pytest.raises(AssertionError):
        reset_kind_names(struct, names)


def test_prepare_for_spglib(db_test_app):
    structure_data = {
        "lattice": [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
        "ccoords": [[0, 0, 0], [0.5, 0.5, 0.5], [1, 1, 1], [1.5, 1.5, 1.5]],
        "atomic_numbers": [1, 8, 1, 8],
        "pbc": [True, True, True],
        "equivalent": [1, 0, 2, 0]
    }

    cell, kind_map = prepare_for_spglib(structure_data)
    assert np.allclose(
        cell[0], [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]])
    assert np.allclose(
        cell[1], [[0., 0., 0.], [0.25, 0.25, 0.25],
                  [0.5, 0.5, 0.5], [0.75, 0.75, 0.75]])
    assert cell[2] == [0, 1, 2, 1]
    assert kind_map == {0: 'H1', 1: 'O', 2: 'H2'}


def test_compute_symmetry_simple(db_test_app):
    # MgO
    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
    dataset = compute_symmetry_dataset(
        atoms, symprec=0.01, angle_tolerance=None)
    assert dataset["number"] == 225
    assert len(dataset["rotations"]) == 192


def test_compute_symmetry_with_equivalent(db_test_app):
    struct_data = {
        "lattice": [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
        "ccoords": [[0, 0, 0], [0.5, 0.5, 0.5], [1, 1, 1], [1.5, 1.5, 1.5]],
        "atomic_numbers": [1, 8, 1, 8],
        "pbc": [True, True, True],
        "equivalent": [1, 0, 1, 0]
    }
    dataset = compute_symmetry_dataset(
        struct_data, symprec=0.01, angle_tolerance=None)
    assert dataset["number"] == 166
    assert len(dataset["rotations"]) == 24


def test_compute_symmetry_no_equivalent(db_test_app):
    struct_data = {
        "lattice": [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
        "ccoords": [[0, 0, 0], [0.5, 0.5, 0.5], [1, 1, 1], [1.5, 1.5, 1.5]],
        "atomic_numbers": [1, 8, 1, 8],
        "pbc": [True, True, True],
        "equivalent": [1, 2, 3, 4]
    }
    dataset = compute_symmetry_dataset(
        struct_data, symprec=0.01, angle_tolerance=None)
    assert dataset["number"] == 160
    assert len(dataset["rotations"]) == 6


def test_find_primitive(db_test_app):
    # MgO
    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
    struct = find_primitive(atoms, symprec=0.01, angle_tolerance=None)
    dataset = compute_symmetry_dataset(
        struct, symprec=0.01, angle_tolerance=None)
    assert dataset["number"] == 225
    assert len(dataset["rotations"]) == 48


def test_standardize_cell(db_test_app):
    # MgO
    atoms = crystal(
        symbols=[12, 8],
        basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
        spacegroup=225,
        cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
    struct = standardize_cell(atoms, symprec=0.01, angle_tolerance=None,
                              to_primitive=True)
    dataset = compute_symmetry_dataset(
        struct, symprec=0.01, angle_tolerance=None)
    assert dataset["number"] == 225
    assert len(dataset["rotations"]) == 48


def test_get_hall_number_from_symmetry():
    assert get_hall_number_from_symmetry(
        [[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
         [-1, 0, 0, 0, -1, 0, 0, 0, -1, 0, 0, 0]]) == 2


def test_operation_transforms():

    # from nio_sto3g_afm.crystal.gui
    lattice = [[0.000000000E+00, -2.082000000E+00, -2.082000000E+00],
               [0.000000000E+00, -2.082000000E+00, 2.082000000E+00],
               [-4.164000000E+00, 0.000000000E+00, 0.000000000E+00]]

    known_cart_ops = [
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, -2.082, -2.082],
        [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0, -2.082, -2.082],
        [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, -2.082, -2.082],
        [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0, -2.082, -2.082],
        [-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, -2.082, -2.082],
        [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0, -2.082, -2.082],
        [-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0, -2.082, -2.082],
        [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0, -2.082, -2.082],
        [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    ]

    # from nio_sto3g_afm.crystal.out
    known_frac_ops = [
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    ]

    # convert from frac to cart
    cart_ops = operations_frac_to_cart(known_frac_ops, lattice)
    if not np.allclose(
            np.sort(known_cart_ops, axis=0),
            np.sort(cart_ops, axis=0)):
        raise AssertionError(
            np.sort(known_cart_ops, axis=0) == np.sort(cart_ops, axis=0)
        )
    # assert not difference_ops(cart_ops, known_cart_ops)

    # convert from cart to frac
    frac_ops = operations_cart_to_frac(known_cart_ops, lattice)
    if not np.allclose(
            np.sort(known_frac_ops, axis=0),
            np.sort(frac_ops, axis=0)):
        raise AssertionError(
            np.sort(known_frac_ops, axis=0) == np.sort(frac_ops, axis=0)
        )
    # assert not difference_ops(frac_ops, known_frac_ops)

    # convert back
    frac_ops2 = operations_cart_to_frac(cart_ops, lattice)
    if not np.allclose(
            np.sort(known_frac_ops, axis=0),
            np.sort(frac_ops2, axis=0)):
        raise AssertionError(
            np.sort(known_frac_ops, axis=0) == np.sort(frac_ops2, axis=0)
        )
    # assert not difference_ops(frac_ops2, known_frac_ops)
    cart_ops2 = operations_frac_to_cart(frac_ops, lattice)
    if not np.allclose(
            np.sort(known_cart_ops, axis=0),
            np.sort(cart_ops2, axis=0)):
        raise AssertionError(
            np.sort(known_cart_ops, axis=0) == np.sort(cart_ops2, axis=0)
        )
    # assert not difference_ops(cart_ops2, known_cart_ops)
