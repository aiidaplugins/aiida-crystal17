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
"""Plugin for running CRYSTAL17 properties computations."""


from aiida.plugins import DataFactory

from aiida_crystal17.calculations.prop_abstract import PropAbstractCalculation
from aiida_crystal17.parsers.raw.doss_input import create_doss_content
from aiida_crystal17.parsers.raw.prop_inputs import create_rotref_content
from aiida_crystal17.validation import validate_against_schema


def _validate_inputs(dict_data):
    validate_against_schema(dict_data.get_dict(), 'prop.doss.schema.json')


class CryDossCalculation(PropAbstractCalculation):
    """
    AiiDA calculation plugin to run the ``properties`` executable,
    for DOSS calculations.
    """

    @classmethod
    def validate_parameters(cls, data):
        dct = data.get_dict()
        k_points = dct.pop('k_points')
        validate_against_schema({'k_points': k_points}, 'prop.newk.schema.json')
        if 'ROTREF' in dct:
            rotref = dct.pop('ROTREF')
            validate_against_schema({'ROTREF': rotref}, 'prop.rotref.schema.json')
        validate_against_schema(dct, 'prop.doss.schema.json')

    @classmethod
    def define(cls, spec):
        super(CryDossCalculation, cls).define(spec)

        spec.input('metadata.options.output_isovalue_fname', valid_type=str, default='fort.25')

        spec.input('metadata.options.parser_name', valid_type=str, default='crystal17.doss')

        spec.exit_code(352,
                       'ERROR_ISOVALUE_FILE_MISSING',
                       message='parser could not find the output isovalue (fort.25) file')
        spec.exit_code(353, 'ERROR_PARSING_ISOVALUE_FILE', message='error parsing output isovalue (fort.25) file')

        spec.output('arrays', valid_type=DataFactory('array'), required=False, help='energies and DoS arrays')

    def create_input_content(self):
        dct = self.inputs.parameters.get_dict()
        lines = self.create_newk_lines(dct)
        lines.extend(create_rotref_content(dct, validate=False))
        lines.extend(create_doss_content(dct))
        return '\n'.join(lines)

    def get_retrieve_list(self):
        return [self.metadata.options.stdout_file_name, self.metadata.options.output_isovalue_fname]

    def get_retrieve_temp_list(self):
        return []
