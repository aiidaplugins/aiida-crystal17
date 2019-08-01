#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Chris Sewell
#
# This file is part of aiida-crystal17.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions
# of version 3 of the GNU Lesser General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
import numpy as np

from aiida_crystal17.symmetry import convert_structure, operation_cart_to_frac
from aiida_crystal17.parsers.raw.parse_fort34 import get_crystal_type_name
from aiida_crystal17.validation import validate_against_schema


def create_geometry_lines(structure_data, symmetry_data=None, name='main-geometry'):
    """ create list of lines for geometry section of .gin

    Parameters
    ----------
    structure_data: aiida.StructureData or dict or ase.Atoms
        dict with keys: 'pbc', 'atomic_numbers', 'ccoords', 'lattice',
        or ase.Atoms, or any object that has method structure_data.get_ase()
    symmetry_data: dict or None
        keys; 'operations', 'basis', 'crystal_type_name'/'hall_number'
    name: str
        name to assign geometry

    Returns
    -------
    list[str]

    """
    lines = ['name {}'.format(name)]
    atoms = convert_structure(structure_data, 'ase')

    if sum(atoms.get_pbc()) == 1:
        if symmetry_data is not None:
            raise NotImplementedError('cannot set symmetry data for 1D structures')
        return create_1d_geometry(lines, atoms)

    if not all(atoms.get_pbc()):
        # TODO For 2D use svectors and sfractional,
        # can you specify symmetry operations?
        raise NotImplementedError('2-D periodicity')

    if symmetry_data is None:
        pass
        # symmetry_data = structure_to_symmetry(structure_data)
    else:
        validate_against_schema(symmetry_data, 'symmetry.schema.json')

    # add cell vectors
    lines.append('vectors')
    for vector in atoms.cell:
        lines.append('{0:.6f} {1:.6f} {2:.6f}'.format(*vector))

    # add atomic sites
    lines.append('cartesian')

    if symmetry_data is not None:
        # if symmetry operations are specified,
        # then only symmetry inequivalent sites should be added
        if 'equivalent_sites' not in symmetry_data:
            raise KeyError("symmetry data does not contain the 'equivalent_sites' key")
        equivalent = symmetry_data['equivalent_sites']
        if atoms.get_number_of_atoms() != len(equivalent):
            raise ValueError('number of atomic sites != number of symmetry equivalent sites')
        used_equivalents = []
        for site, eq in zip(atoms, equivalent):
            if eq not in used_equivalents:
                lines.append('{0} core {1:.6f} {2:.6f} {3:.6f}'.format(site.symbol, *site.position))
                used_equivalents.append(eq)
    else:
        for site in atoms:
            lines.append('{0} core {1:.6f} {2:.6f} {3:.6f}'.format(site.symbol, *site.position))

    # TODO creating shell models

    # TODO could also use `spacegroup` (and `origin`) to set symmetry

    # add crystal type of symmetry
    if symmetry_data is not None:
        hall_number = symmetry_data.get('hall_number', None)
        crystal_type_name = symmetry_data.get('crystal_type_name', None)
        if crystal_type_name is None and hall_number is not None:
            crystal_type_name = get_crystal_type_name(hall_number)
        if crystal_type_name is not None:
            if crystal_type_name in ['trigonal', 'rhombohedral']:
                crystal_type_name = 'hexagonal'
            assert crystal_type_name in [
                'triclinic', 'monoclinic', 'orthorhombic', 'tetragonal', 'hexagonal', 'rhombohedral', 'cubic'
            ], crystal_type_name
            lines.append('symmetry_cell {}'.format(crystal_type_name))

    # add symmetry operations
    if symmetry_data is not None:
        operations = symmetry_data['operations']
        if operations and symmetry_data['basis'] == 'cartesian':
            operations = operation_cart_to_frac(operations, atoms.cell)

        for op in operations:
            if np.allclose(op, [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]):
                # identity matrix is not required
                continue
            lines.append('symmetry_operator')
            lines.append('{0:8.5f} {1:8.5f} {2:8.5f} {3:8.5f}'.format(op[0], op[3], op[6], op[9]))
            lines.append('{0:8.5f} {1:8.5f} {2:8.5f} {3:8.5f}'.format(op[1], op[4], op[7], op[10]))
            lines.append('{0:8.5f} {1:8.5f} {2:8.5f} {3:8.5f}'.format(op[2], op[5], op[8], op[11]))

    return lines


def create_1d_geometry(lines, atoms):
    """ create 1D (polymer) geometry lines """
    # TODO creating shell models
    validate_1d_geometry(atoms)
    lines.append('pcell')
    lines.append('{0:.6f}'.format(atoms.cell[0][0]))
    lines.append('pfractional')
    symbols = atoms.get_chemical_symbols()
    fcoords = atoms.get_scaled_positions()
    ccoords = atoms.positions
    for symbol, fcoords, ccoords in zip(symbols, fcoords, ccoords):
        lines.append('{0} core {1:.6f} {2:.6f} {3:.6f}'.format(symbol, fcoords[0], ccoords[1], ccoords[2]))
    return lines


def validate_1d_geometry(structure):
    """ validate a 1-d structure """
    if not list(structure.pbc) == [True, False, False]:
        raise NotImplementedError('a 1-D structure can only be periodic in the x-direction')
    expected_cell = np.eye(3)
    for i in range(3):
        expected_cell[i][i] = structure.cell[i][i]
    if not np.allclose(structure.cell, expected_cell):
        raise NotImplementedError('a 1-D structure cell must be of the form '
                                  '[[x, 0, 0], [0, y, 0], [0, 0, z]]: {}'.format(structure.cell))
