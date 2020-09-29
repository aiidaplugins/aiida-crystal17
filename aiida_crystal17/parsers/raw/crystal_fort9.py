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
from collections import namedtuple

from scipy.io import FortranFile

from aiida_crystal17.common.parsing import convert_units

RECORD_DTYPES = (
    "int32",
    "float64",
    "int32",
    "int32",
    "float64",
    "float64",
    "int32",
    "float64",
    "float64",
)

Fort9Results = namedtuple(
    "Fort9Results",
    [
        "cell",
        "atomic_numbers",
        "positions",
        "transform_matrix",
        "n_symops",
        "n_orbitals",
    ],
)


def parse_fort9(file_obj, length_units="angstrom"):
    """Parse data from the fort.9 wavefunction.

    Parameters
    ----------
    file_obj : str or file-like
        filepath or file opened in binary mode
    length_units : str
        units to return cell and position lengths ('bohr' or 'angstrom')

    Returns
    -------
    Fort9Results

    """
    if isinstance(file_obj, str):
        with FortranFile(file_obj) as handle:
            data = [handle.read_record(rtype) for rtype in RECORD_DTYPES]
    else:
        data = [FortranFile(file_obj).read_record(rtype) for rtype in RECORD_DTYPES]

    cell = convert_units(data[5][:9].reshape(3, 3), "bohr", length_units).tolist()
    atomic_numbers = data[7].astype(int).tolist()
    positions = convert_units(
        data[8].reshape(len(atomic_numbers), 3), "bohr", length_units
    ).tolist()

    transform_matrix = data[5][9:18].reshape(3, 3).tolist()
    symops_id = data[6].tolist()
    n_symops = len(symops_id)
    # TODO need to verify these symops are correct, and what basis they are in
    # symops_rot = data[5][18:18 + n_symops * 9].reshape(n_symops, 3, 3).tolist()
    # symops_tr = data[5][18 + n_symops * 9:].reshape(n_symops, 3).tolist()

    n_orbitals = int(data[3][6])

    return Fort9Results(
        cell, atomic_numbers, positions, transform_matrix, n_symops, n_orbitals
    )
