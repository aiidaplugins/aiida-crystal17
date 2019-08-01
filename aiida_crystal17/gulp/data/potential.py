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
from hashlib import md5
import json

import six

from aiida.common import exceptions
from aiida.orm import Data
from aiida.plugins.entry_point import load_entry_point, get_entry_point_names


class EmpiricalPotential(Data):
    """
    Store the empirical potential data
    """
    entry_name = 'gulp.potentials'
    _default_potential_filename = 'potential.pot'
    _default_potential_json = 'potential.json'
    _default_fitting_json = 'fitting.json'

    @classmethod
    def list_pair_styles(cls):
        return get_entry_point_names(cls.entry_name)

    @classmethod
    def load_pair_style(cls, entry_name):
        return load_entry_point(cls.entry_name, entry_name)

    def __init__(self, pair_style, potential_data, **kwargs):
        # pair_style = kwargs.pop('pair_style', None)
        # potential_data = kwargs.pop('data', None)
        additional_data = kwargs.pop('additional', None)
        fitting_data = kwargs.pop('fitting_data', None)
        super(EmpiricalPotential, self).__init__(**kwargs)
        self.set_data(pair_style, potential_data, fitting_data, additional_data)

    def set_data(self, pair_style, potential_data, fitting_data=None, additional_data=None):
        """
        Store the potential type (ex. Tersoff, EAM, LJ, ..) and data
        """
        # TODO add filtering by elements (possibly by supplying a structure?)
        if pair_style is None:
            raise ValueError("'pair_style' must be provided")
        if pair_style not in self.list_pair_styles():
            raise ValueError("'pair_style' must be in: {}".format(self.list_pair_styles()))
        potential_writer = self.load_pair_style(pair_style)()

        description = potential_writer.get_description()
        output = potential_writer.create_content(potential_data, fitting_data=fitting_data)

        with self.open(self._default_potential_filename, 'w') as handle:
            handle.write(six.ensure_text(output.content))

        with self.open(self._default_potential_json, 'w') as handle:
            handle.write(six.ensure_text(json.dumps(potential_data)))

        if fitting_data is not None:
            with self.open(self._default_fitting_json, 'w') as handle:
                handle.write(six.ensure_text(json.dumps(fitting_data)))

        dictionary = {
            'pair_style': pair_style,
            'description': description,
            'species': potential_data['species'],
            'input_lines_md5': md5(output.content.encode('utf-8')).hexdigest(),
            'fitting_flags': fitting_data is not None,
            'total_flags': output.number_of_flags,
            'number_flagged': output.number_flagged,
            'potential_filename': self._default_potential_filename,
            'potential_json': self._default_potential_json,
            'fitting_json': self._default_fitting_json
        }
        if additional_data is not None:
            dictionary['additional'] = additional_data

        dictionary_backup = copy.deepcopy(self.attributes)

        try:
            # Clear existing attributes and set the new dictionary
            self.clear_attributes()
            self._update_dict(dictionary)
        except exceptions.ModificationNotAllowed:  # pylint: disable=try-except-raise
            # I reraise here to avoid to go in the generic 'except' below that would raise the same exception again
            raise
        except Exception:
            # Try to restore the old data
            self.clear_attributes()
            self._update_dict(dictionary_backup)
            raise

    def _update_dict(self, dictionary):
        """Update the current dictionary with the keys provided in the dictionary.

        .. note:: works exactly as `dict.update()` where new keys are simply added and existing keys are overwritten.

        :param dictionary: a dictionary with the keys to substitute
        """
        for key, value in dictionary.items():
            self.set_attribute(key, value)

    def get_potential_dict(self):
        """Return a dictionary with the parameters currently set.

        :rtype: dict
        """
        potential_json = self.get_attribute('potential_json')
        if potential_json not in self.list_object_names():
            raise KeyError('potential dict not set for node pk={}'.format(self.pk))

        with self.open(potential_json, mode='r') as handle:
            data = json.load(handle)

        return data

    def get_fitting_dict(self):
        """Return a dictionary with the parameters currently set.

        :rtype: dict
        """
        fitting_json = self.get_attribute('fitting_json')
        if fitting_json not in self.list_object_names():
            raise KeyError('fitting dict not set for node pk={}'.format(self.pk))

        with self.open(fitting_json, mode='r') as handle:
            data = json.load(handle)

        return data

    @property
    def pair_style(self):
        return self.get_attribute('pair_style')

    @property
    def species(self):
        return self.get_attribute('species')

    @property
    def has_fitting_flags(self):
        return self.get_attribute('fitting_flags')

    @property
    def number_of_variables(self):
        return self.get_attribute('number_flagged')

    @property
    def input_lines_md5(self):
        return self.get_attribute('input_lines_md5')

    def get_description(self):
        return str(self.pair_style)

    def get_input_lines(self):
        potential_filename = self.get_attribute('potential_filename')
        if potential_filename not in self.list_object_names():
            raise KeyError('potential file not set for node pk={}'.format(self.pk))

        with self.open(potential_filename, mode='r') as handle:
            lines = handle.read()

        return lines.splitlines()
