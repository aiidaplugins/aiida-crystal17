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
"""Parse gaussian cube files, e.g. DENSCUBE.DAT, SPINCUBE.DAT, POTCUBE.DAT.

The specification can be found at:
http://h5cube-spec.readthedocs.io/en/latest/cubeformat.html
"""
from collections import namedtuple

import numpy as np

from aiida_crystal17.common.parsing import convert_units, split_numbers

GcubeResult = namedtuple('GcubeResult', [
    'header', 'cell', 'voxel_cell', 'voxel_grid', 'origin', 'atoms_positions', 'atoms_nuclear_charge',
    'atoms_atomic_number', 'units', 'density'
])


def read_gaussian_cube(handle, return_density=False, dist_units='angstrom'):
    """Parse gaussian cube files to a data structure.

    The specification can be found at:
    http://h5cube-spec.readthedocs.io/en/latest/cubeformat.html

    CRYSTAL outputs include DENSCUBE.DAT, SPINCUBE.DAT, POTCUBE.DAT.

    Parameters
    ----------
    handle : file-like
        an open file handle
    return_density : bool
        whether to read and return the density values
    dist_units : str
        the distance units to return

    Returns
    -------
    aiida_crystal17.parsers.raw.gaussian_cube.GcubeResult

    """
    in_dunits = 'bohr'

    header = [handle.readline().strip(), handle.readline().strip()]
    settings = split_numbers(handle.readline().strip())

    if len(settings) > 4 and settings[4] != 1:
        # TODO implement NVAL != 1
        raise NotImplementedError('not yet implemented NVAL != 1')

    natoms = settings[0]
    origin = convert_units(np.array(settings[1:4]), in_dunits, dist_units)
    if natoms < 0:
        # TODO implement DSET_IDS
        raise NotImplementedError('not yet implemented DSET_IDS')
    an, ax, ay, az = split_numbers(handle.readline().strip())
    bn, bx, by, bz = split_numbers(handle.readline().strip())
    cn, cx, cy, cz = split_numbers(handle.readline().strip())

    voxel_cell = convert_units(np.array([[ax, ay, az], [bx, by, bz], [cx, cy, cz]]), in_dunits, dist_units)

    avec = convert_units(np.array([ax, ay, az]) * an, in_dunits, dist_units)
    bvec = convert_units(np.array([bx, by, bz]) * bn, in_dunits, dist_units)
    cvec = convert_units(np.array([cx, cy, cz]) * cn, in_dunits, dist_units)

    atomic_numbers = []
    nuclear_charges = []
    ccoords = []
    for _ in range(int(natoms)):
        anum, ncharge, x, y, z = split_numbers(handle.readline().strip())
        atomic_numbers.append(int(anum))
        nuclear_charges.append(ncharge)
        ccoord = convert_units(np.asarray([x, y, z]), in_dunits, dist_units) - origin
        ccoords.append(ccoord.tolist())

    density = None
    if return_density:
        values = []
        for line in handle:
            values += line.split()
        density = np.array(values, dtype=float).reshape((int(an), int(bn), int(cn)))

    return GcubeResult(
        header,
        [avec.tolist(), bvec.tolist(), cvec.tolist()],
        voxel_cell.tolist(),
        [int(an), int(bn), int(cn)],
        origin.tolist(),
        ccoords,
        nuclear_charges,
        atomic_numbers,
        {
            'conversion': 'CODATA2014',
            'length': dist_units,
        },
        density
    )  # yapf: disable
