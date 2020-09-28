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
"""Aiida data type to store a gaussian cube."""
import io
import os
import tempfile
from contextlib import contextmanager
from zipfile import ZIP_DEFLATED, ZipFile

import ase
import numpy as np


from aiida.orm import Data

from aiida_crystal17.common import SYMBOLS
from aiida_crystal17.parsers.raw.gaussian_cube import read_gaussian_cube


class GaussianCube(Data):
    """Aiida data type to store a gaussian cube.

    The file is stored within a compressed zip folder, reducing storage space.

    The specification can be found at:
    http://h5cube-spec.readthedocs.io/en/latest/cubeformat.html

    CRYSTAL outputs include DENSCUBE.DAT, SPINCUBE.DAT, POTCUBE.DAT.

    """

    _zip_filename = 'gcube.zip'
    _cube_filename = 'gaussian.cube'
    _compression_method = ZIP_DEFLATED

    def __init__(self, fileobj, binary=True, **kwargs):
        """Store a gaussian cube file.

        Parameters
        ----------
        fileobj : str or file-like
            the file or path to the file
        binary : bool
            whether the file is opened in binary mode

        """
        super(GaussianCube, self).__init__(**kwargs)

        if isinstance(fileobj, str):
            self.set_from_filepath(fileobj)
        else:
            self.set_from_fileobj(fileobj, binary=binary)

    def set_from_filepath(self, filepath):
        """Store a gaussian cube file, given a path to the file.

        Parameters
        ----------
        filepath : str

        """
        self.reset_attributes({})

        # read the header of the file
        with io.open(filepath, 'r') as handle:
            cube_data = read_gaussian_cube(handle, return_density=False, dist_units='angstrom')

        # Write the zip to a temporary file, and then add it to the node repository
        with tempfile.NamedTemporaryFile() as temp_handle:
            with ZipFile(temp_handle, 'w', self._compression_method) as zip_file:
                zip_file.write(filepath, arcname=self._cube_filename)

            # Flush and rewind the temporary handle,
            # otherwise the command to store it in the repo will write an empty file
            temp_handle.flush()
            temp_handle.seek(0)

            self.put_object_from_filelike(temp_handle, self._zip_filename, mode='wb', encoding=None)

        # store information about the zip file
        self.set_attribute('zip_filename', self._zip_filename)
        self.set_attribute('cube_filename', self._cube_filename)
        self.set_attribute('compression_method', self._compression_method)

        # store some basic information about the cube
        self.set_attribute('cell', cube_data.cell)
        self.set_attribute('header', cube_data.header)
        self.set_attribute('voxel_grid', cube_data.voxel_grid)
        self.set_attribute('units', cube_data.units)
        self.set_attribute('elements', list(sorted([SYMBOLS.get(n, n) for n in set(cube_data.atoms_atomic_number)])))

    def set_from_fileobj(self, fileobj, binary=True):
        """Store a gaussian cube file, given a handle to the file.

        Parameters
        ----------
        fileobj : file-like
        binary : bool
            whether the file is opened in binary mode

        """
        path = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb' if binary else 'w', delete=False) as temp_handle:
                temp_handle.write(fileobj.read())
                path = temp_handle.name
            self.set_from_filepath(path)
        finally:
            if path:
                os.remove(path)

    @contextmanager
    def open_cube_file(self, binary=False):
        """Open a file handle to the gaussian cube file."""
        zip_filename = self.get_attribute('zip_filename')
        compression_method = self.get_attribute('compression_method')
        cube_filename = self.get_attribute('cube_filename')

        with self.open(zip_filename, mode='rb') as handle:
            with ZipFile(handle, 'r', compression_method) as zip_file:
                with zip_file.open(cube_filename) as file_handle:
                    if binary:
                        yield file_handle
                    else:
                        yield io.TextIOWrapper(file_handle)

    def get_cube_data(self, return_density=False, dist_units='angstrom'):
        """Parse gaussian cube files to a data structure.

        Parameters
        ----------
        return_density : bool
            whether to read and return the density values
        dist_units : str
            the distance units to return

        Returns
        -------
        aiida_crystal17.parsers.raw.gaussian_cube.GcubeResult

        """
        # TODO cache
        with self.open_cube_file() as handle:
            cube_data = read_gaussian_cube(handle, return_density=return_density, dist_units=dist_units)
        return cube_data

    def get_ase(self, pbc=(True, True, True)):
        """Return the ``ase.Atoms`` for the structure."""
        cube_data = self.get_cube_data(return_density=False, dist_units='angstrom')
        return ase.Atoms(cell=cube_data.cell,
                         positions=cube_data.atoms_positions,
                         numbers=cube_data.atoms_atomic_number,
                         pbc=pbc)

    def compute_integration_cell(self):
        """Integrate the density over the full cell."""
        data = self.get_cube_data(return_density=True)
        voxel_volume = np.linalg.det(data.voxel_cell)
        return np.sum(data.density) * voxel_volume

    def compute_integration_sphere(self, positions, radius, pbc=(True, True, True)):
        """Integrate the density over a sphere.

        Parameters
        ----------
        positions : list
            (x, y, z) or list of (x, y, z)
        radius : float
            must be less than the shortest periodic cell vector length
        pbc : list[bool]
            periodic dimensions

        Returns
        -------
        float

        """
        assert np.array(pbc).shape == (3,)
        if np.array(positions).shape == (3,):
            positions = [positions]
        positions = np.array(positions)
        assert len(positions.shape) == 2 and positions.shape[1] == 3

        data = self.get_cube_data(return_density=True)

        voxel_volume = np.linalg.det(data.voxel_cell)

        # account for periodic boundaries
        plengths = [l for p, l in zip(pbc, np.linalg.norm(data.cell, axis=1)) if p]
        if plengths and radius > min(plengths):
            raise ValueError('The radius must be less than the shortest periodic cell vector ({0:.2f})'.format(
                min(plengths)))

        # TODO this could be made more efficient, e.g. by tessellating according to the quadrant the position is in
        density = np.tile(data.density, [3 if p else 1 for p in pbc])
        offset_positions = positions
        for i, is_periodic in enumerate(pbc):
            if is_periodic:
                offset_positions = offset_positions + np.array(data.cell[i])

        # get values and coordinates for each voxel
        values = np.array([v for (x, y, z), v in np.ndenumerate(density)])
        indices = [[x, y, z] for (x, y, z), v in np.ndenumerate(density)]
        coordinates = np.dot(indices, data.voxel_cell) - np.array(data.origin)

        # get distance squared to each voxel
        final_values = []
        for offset_position in offset_positions:
            dist_sq = ((coordinates - offset_position)**2).sum(1)
            # TODO integrating voxels that are partially within the sphere?
            final_values.append(np.sum(values[dist_sq <= (radius**2)]) * voxel_volume)

        return final_values

    def compute_integration_atom(self, indices, radius, pbc=(True, True, True)):
        """Integrate the density over a sphere.

        Parameters
        ----------
        indices : int or list[int]
        radius : float or list[float]
            radius for all atoms or per cell
            must be less than the shortest periodic cell vector length
        pbc : list[bool]
            periodic dimensions

        Returns
        -------
        float

        """
        if isinstance(indices, int):
            indices = [indices]
        indices = np.array(indices)
        data = self.get_cube_data(return_density=False)
        return self.compute_integration_sphere(np.array(data.atoms_positions)[indices], radius=radius, pbc=pbc)
