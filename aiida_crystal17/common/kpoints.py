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


def create_kpoints_from_distance(structure, distance, force_parity=True):
    """
    Generate a uniformly spaced kpoint mesh for a given structure where the spacing between kpoints in reciprocal
    space is guaranteed to be at least the defined distance.

    :param structure: the StructureData to which the mesh should apply
    :param distance: a float with the desired distance between kpoints in reciprocal space
    :param force_parity: a bool to specify whether the generated mesh should maintain parity
    :returns: a KpointsData with the generated mesh
    """
    from numpy import linalg
    from aiida.orm import KpointsData

    epsilon = 1E-5

    kpoints = KpointsData()
    kpoints.set_cell_from_structure(structure)
    kpoints.set_kpoints_mesh_from_density(distance, force_parity=force_parity)

    lengths_vector = [linalg.norm(vector) for vector in structure.cell]
    lengths_kpoint = kpoints.get_kpoints_mesh()[0]

    is_symmetric_cell = all(abs(length - lengths_vector[0]) < epsilon for length in lengths_vector)
    is_symmetric_mesh = all(length == lengths_kpoint[0] for length in lengths_kpoint)

    # If the vectors of the cell all have the same length, the kpoint mesh should be isotropic as well
    if is_symmetric_cell and not is_symmetric_mesh:
        nk = max(lengths_kpoint)
        kpoints.set_kpoints_mesh([nk, nk, nk])

    return kpoints
