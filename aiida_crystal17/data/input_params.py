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

from aiida.common.utils import classproperty
from aiida.orm import Data

from aiida_crystal17.validation import load_schema, validate_against_schema
from aiida_crystal17.common import unflatten_dict


class CryInputParamsData(Data):
    """stores a validated dictionary of input parameters for CryMainCalculations"""
    _data_schema = None

    @classproperty
    def data_schema(cls):
        """ return the data schema,
        which is loaded from file the first time it is called"""
        if cls._data_schema is None:
            cls._data_schema = load_schema('inputd12.schema.json')
        return copy.deepcopy(cls._data_schema)

    @classmethod
    def validate_parameters(cls, dct):
        """validate an input dictionary

        Parameters
        ----------
        dct : dict

        """
        validate_against_schema(dct, cls.data_schema)

    def __init__(self, data=None, unflatten=False, **kwargs):
        """stores a validated dictionary of input parameters for CryMainCalculations

        Parameters
        ----------
        data : dict
            the data to set
        unflatten : bool
            whether to unflatten the dictionary, e.g. from {"a.b": 1} to {"a": {"b": 1}}

        """
        super(CryInputParamsData, self).__init__(**kwargs)
        if data is not None:
            if unflatten:
                data = unflatten_dict(data)
            self.set_data(data)

    def _validate(self):
        super(CryInputParamsData, self)._validate()

        self.validate_parameters(self.get_dict())

        return True

    def set_data(self, data):
        """
        Replace the current data with another one.

        :param data: The dictionary to set.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        # first validate the inputs
        self.validate_parameters(data)

        # store all but the symmetry operations as attributes
        backup_dict = copy.deepcopy(dict(self.attributes))

        try:
            # Clear existing attributes and set the new dictionary
            self._update_attributes(data)
        except ModificationNotAllowed:  # pylint: disable=try-except-raise
            # I re-raise here to avoid to go in the generic 'except' below that
            # would raise the same exception again
            raise
        except Exception:
            # Try to restore the old data
            self.clear_attributes()
            self._update_attributes(backup_dict)
            raise

    def _update_attributes(self, data):
        """
        Update the current attribute with the keys provided in the dictionary.

        :param data: a dictionary with the keys to substitute. It works like
          dict.update(), adding new keys and overwriting existing keys.
        """
        for k, v in data.items():
            self.set_attribute(k, v)

    def get_dict(self):
        """Return a dictionary with the parameters currently set.

        :rtype: dict

        """
        return dict(self.attributes)

    @property
    def data(self):
        """Return an instance of `AttributeManager`
        that transforms the dictionary into an attribute dict.

        .. note:: this will allow one to do `node.dict.key`
                  as well as `node.dict[key]`.

        :return: an instance of the `AttributeResultManager`.
        """
        from aiida.orm.utils.managers import AttributeManager
        return AttributeManager(self)
