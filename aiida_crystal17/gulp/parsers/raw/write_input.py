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
import hashlib
import io

import six

from aiida_crystal17.validation import validate_against_schema
from aiida_crystal17.gulp.unit_styles import get_pressure
from aiida_crystal17.gulp.parsers.raw.write_geometry import create_geometry_lines


class InputCreationBase(object):
    """a base class for creating a main.gin input file for GULP.
    Sub-classes can override the methods:
    ``validate_parameters``, ``get_input_keywords``, ``get_input_keywords``

    """

    def __init__(self, outputs=None):
        """create a main.gin input file for GULP

        Parameters
        ----------
        outputs : dict or None
            mapping of type of output to filename, e.g. {"cif": "output.cif"}

        """
        self._outputs = {} if outputs is None else outputs
        self._content_lines = None
        self._encoding = 'utf-8'

    def get_content(self):
        if self._content_lines is None:
            raise ValueError('content has not been set')
        return '\n'.join(self._content_lines)

    def get_content_lines(self):
        if self._content_lines is None:
            raise ValueError('content has not been set')
        return self._content_lines[:]

    def get_content_hash(self):
        """get md5 hex hash of content"""
        content = self.get_content()
        return hashlib.md5(six.u(content).encode(self._encoding)).hexdigest()

    def write_content(self, file_like):
        """write the content to file_like object
        (path string or object with `write` method)
        """
        content = six.u(self.get_content())
        if isinstance(file_like, six.string_types):
            with io.open(file_like, 'w', encoding=self._encoding) as handle:
                handle.write(content)
        else:
            file_like.write(content)

    def validate_parameters(self, parameters):
        """validate the parameters dict, supplied to ``create_content``

        Parameters
        ----------
        parameters : dict
            the paramaters dict

        Returns
        -------
        bool
            True if validation is successful

        """
        return True

    def get_input_keywords(self, parameters):
        """return list of keywords for header, e.g.

        'verb': verbose detail, including energy contributions
        'operators': prints out symmetry operations
        'prop': print properties, incl bulk/shear modulus, dielectric
        'linmin': print details of minimisation
        'comp': print intital/final geometry comparison

        Parameters
        ----------
        parameters : dict
            the paramaters dict

        Returns
        -------
        list[str]
            list of keywords

        """
        return ['verb']

    def get_other_option_lines(self, parameters):
        """get list of other option lines for .gin

        Parameters
        ----------
        parameters : dict
            additional parameter data

        Returns
        -------
        list[str]

        """
        return []

    def create_content(self, structure, potential_lines, parameters=None, symmetry=None):
        """create main input content for gulp.in

        Parameters
        ----------
        structure : aiida.StructureData
            the input structure
        potential_lines: list[str]
        parameters : aiida.orm.nodes.data.dict.Dict or dict
            additional parameter data, by default None
        symmetry : aiida.orm.nodes.data.dict.Dict or dict
            data regarding the structure symmetry, by default None

        Returns
        -------
        list[str]
            file content

        """
        # convert inputs to dictionaries
        if parameters is None:
            parameters = {}
        else:
            if hasattr(parameters, 'get_dict'):
                parameters = parameters.get_dict()
        if symmetry is not None:
            if hasattr(symmetry, 'get_dict'):
                symmetry = symmetry.get_dict()

        # validation
        self.validate_parameters(parameters)

        content = []

        # keywords
        content.append(' '.join(self.get_input_keywords(parameters)))
        content.append('')

        # TITLE
        if 'title' in parameters:
            content.append('title')
            content.append('{}'.format(parameters['title']))
            content.append('end')
            content.append('')

        # GEOMETRY
        content.append('# Geometry')
        content.extend(self.get_geometry_lines(structure, symmetry))
        content.append('')
        # TODO kind specific inputs (e.g. initial charge)?

        # FORCE FIELD
        content.append('# Force Field')
        content.extend(potential_lines)
        content.append('')

        # OTHER OPTIONS
        other_opts = self.get_other_option_lines(parameters)
        if other_opts:
            content.append('# Other Options')
            content.extend(other_opts)
            content.append('')

        # EXTERNAL OUTPUT OPTIONS
        if self._outputs:
            content.append('# External Outputs')
            for out_type, fname in self._outputs.items():
                content.append('output {0} {1}'.format(out_type, fname))
            content.append('')

        self._content_lines = content
        return content

    @staticmethod
    def get_geometry_lines(structure_data, symmetry_data=None):
        """ create list of lines for geometry section of .gin

        Parameters
        ----------
        structure_data: aiida.StructureData or dict or ase.Atoms
            dict with keys: 'pbc', 'atomic_numbers', 'ccoords', 'lattice',
            or ase.Atoms, or any object that has method structure_data.get_ase()
        symmetry_data: dict or None
            keys; 'operations', 'basis', 'crystal_type_name'/'hall_number'

        Returns
        -------
        list[str]

        """
        return create_geometry_lines(structure_data, symmetry_data=symmetry_data)


class InputCreationSingle(InputCreationBase):
    pass


class InputCreationOpt(InputCreationBase):

    def validate_parameters(self, parameters):
        validate_against_schema(parameters, 'gulp_optimize.schema.json')

    def get_input_keywords(self, parameters):
        keywords = ['optimise', 'verb', parameters['relax']['type']]
        if parameters['minimize']['style'] != 'nr':
            keywords.append(parameters['minimize']['style'])

        # TODO set energy units: eV by default, or use keywords: kcal, kjmol

        # TODO switch between symmetric and non-symmetric
        # if not params.get('symmetry', True):
        #     # Switches off symmetry after generating unit cell
        #     keywords.append('nosymmetry')
        #  	'full' keyword causes the nosymmetry keyword to produce the full,
        # instead of the primitive, unit cell.

        return keywords

    def get_other_option_lines(self, parameters):
        lines = []

        if parameters['relax'].get('pressure', False):
            pressure, punits = get_pressure(parameters['relax']['pressure'], parameters['units'])
            lines.append('pressure {0:.4f} {1}'.format(pressure, punits))
        # NB: Causes energy to be replaced by enthalpy in calculations.

        # maximum number of optimisation steps (default 1000)
        if 'max_iterations' in parameters['minimize']:
            lines.append('maxcyc opt {}'.format(parameters['minimize']['max_iterations']))

        # TODO how do these compare to tolerances from LAMMPS?
        # maximum parameter tolerance (default 0.00001)
        # xtol opt 0.00001
        # maximum function tolerance (default 0.00001)
        # ftol opt 0.00001
        # maximum gradient tolerance (default 0.001)
        # gtol opt 0.001
        # NB: ftol should always be less than gtol
        # maximum allowed individual gradient component (default 0.01)
        # gmax opt 0.01

        return lines
