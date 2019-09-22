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

import six

from aiida.orm import Data

from aiida_crystal17.common import SYMBOLS
from aiida_crystal17.parsers.raw.gaussian_cube import read_gaussian_cube


class GaussianCube(Data):
    """Aiida data type to store a gaussian cube.

    The file is stored within a compressed zip folder, reducing storage space.

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

        if isinstance(fileobj, six.string_types):
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
            data = read_gaussian_cube(handle, return_density=False, dist_units='angstrom')

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
        self.set_attribute_many({k: v for k, v in data.items() if k in ['cell', 'header', 'voxel_grid', 'units']})
        self.set_attribute('elements',
                           list(sorted([SYMBOLS.get(n, n) for n in set(data.get('atoms_atomic_number', []))])))

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
    def open_gcube(self, binary=False):
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
