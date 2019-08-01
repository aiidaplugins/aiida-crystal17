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
import copy
import tempfile

from jsonschema import ValidationError as SchemeError
import numpy as np
import spglib

from aiida.common.utils import classproperty
# from aiida.common.exceptions import ValidationError
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Data

from aiida_crystal17.validation import load_schema, validate_against_schema


class SymmetryData(Data):
    """
    Stores data regarding the symmetry of a structure

    - symmetry operations are stored on file (in the style of ArrayData)
    - the rest of the values (and the number of symmetry operators)
      are stored as attributes in the database

    """
    _ops_filename = 'operations.npy'
    _data_schema = None

    @classproperty
    def data_schema(cls):
        """ return the data schema,
        which is loaded from file the first time it is called"""
        if cls._data_schema is None:
            cls._data_schema = load_schema('symmetry.schema.json')
        return copy.deepcopy(cls._data_schema)

    def __init__(self, **kwargs):
        """Stores the symmetry data for a structure

        - symmetry operations are stored on file (in the style of ArrayData)
        - the rest of the values are stored as attributes in the database

        :param data: the data to set
        """
        data = kwargs.pop('data', None)
        super(SymmetryData, self).__init__(**kwargs)
        if data is not None:
            self.set_data(data)

    def _validate(self):
        super(SymmetryData, self)._validate()

        fname = self._ops_filename
        if fname not in self.list_object_names():
            raise SchemeError('operations not set')

        validate_against_schema(self.get_dict(), self.data_schema)

    def set_data(self, data):
        """
        Replace the current data with another one.

        :param data: The dictionary to set.

        """
        from aiida.common.exceptions import ModificationNotAllowed

        # first validate the inputs
        validate_against_schema(data, self.data_schema)

        # store all but the symmetry operations as attributes
        backup_dict = copy.deepcopy(dict(self.attributes))

        try:
            # Clear existing attributes and set the new dictionary
            self._update_attributes({k: v for k, v in data.items() if k != 'operations'})
            self.set_attribute('num_symops', len(data['operations']))
        except ModificationNotAllowed:  # pylint: disable=try-except-raise
            # I re-raise here to avoid to go in the generic 'except' below that
            # would raise the same exception again
            raise
        except Exception:
            # Try to restore the old data
            self.clear_attributes()
            self._update_attributes(backup_dict)
            raise

        # store the symmetry operations on file
        self._set_operations(data['operations'])

    def _update_attributes(self, data):
        """
        Update the current attribute with the keys provided in the dictionary.

        :param data: a dictionary with the keys to substitute. It works like
          dict.update(), adding new keys and overwriting existing keys.
        """
        for k, v in data.items():
            self.set_attribute(k, v)

    def _set_operations(self, ops):
        fname = self._ops_filename

        if fname in self.list_object_names():
            self.delete_object(fname)

        with tempfile.NamedTemporaryFile() as handle:
            # Store in a temporary file, and then add to the node
            np.save(handle, ops)

            # Flush and rewind the handle, otherwise the command to store it in
            # the repo will write an empty file
            handle.flush()
            handle.seek(0)

            # Write the numpy array to the repository,
            # keeping the byte representation
            self.put_object_from_filelike(handle, fname, mode='wb', encoding=None)

    def _get_operations(self):
        filename = self._ops_filename
        if filename not in self.list_object_names():
            raise KeyError('symmetry operations not set for node pk={}'.format(self.pk))

        # Open a handle in binary read mode as the arrays are written
        # as binary files as well
        with self.open(filename, mode='rb') as handle:
            array = np.load(handle)

        return array.tolist()

    @property
    def data(self):
        """
        Return the data as an AttributeDict
        """
        data = dict(self.attributes)
        if 'num_symops' in data:
            data.pop('num_symops')
        data['operations'] = self._get_operations()
        return AttributeDict(data)

    def get_dict(self):
        """get dictionary of data"""
        data = dict(self.attributes)
        if 'num_symops' in data:
            data.pop('num_symops')
        data['operations'] = self._get_operations()
        return data

    def get_description(self):
        """ return a short string description of the data """
        desc = []
        hall_number = self.get_attribute('hall_number', None)
        num_symops = self.get_attribute('num_symops', None)
        if hall_number is not None:
            desc.append('hall_number: {}'.format(hall_number))
        if num_symops is not None:
            desc.append('symmops: {}'.format(num_symops))
        return '\n'.join(desc)

    @property
    def num_symops(self):
        return self.get_attribute('num_symops', None)

    @property
    def hall_number(self):
        return self.get_attribute('hall_number', None)

    @property
    def spacegroup_info(self):
        """ Translate Hall number to space group type information.
        Returned as an attribute dict
        """
        info = spglib.get_spacegroup_type(self.hall_number)
        if info is None:
            raise ValueError('the hall number could not be converted')
        return AttributeDict(info)

    def add_path(self, src_abs, dst_path):
        from aiida.common.exceptions import ModificationNotAllowed

        raise ModificationNotAllowed('Cannot add files or directories to StructSettingsData object')

    def compare_operations(self, ops, decimal=5):
        """compare operations against stored ones

        :param ops: list of (flattened) symmetry operations
        :param decimal: number of decimal points to round values to
        :returns: dict of differences
        """
        ops_orig = self._get_operations()

        # create a set for each
        ops_orig = set([tuple([round(i, decimal) for i in op]) for op in ops_orig])
        ops_new = set([tuple([round(i, decimal) for i in op]) for op in ops])

        differences = {}
        if ops_orig.difference(ops_new):
            differences['missing'] = ops_orig.difference(ops_new)
        if ops_new.difference(ops_orig):
            differences['additional'] = ops_new.difference(ops_orig)

        return differences
