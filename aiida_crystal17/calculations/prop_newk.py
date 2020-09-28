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


from aiida_crystal17.calculations.prop_abstract import PropAbstractCalculation
from aiida_crystal17.validation import validate_against_schema


class CryNewkCalculation(PropAbstractCalculation):
    """AiiDA calculation plugin to run the properties17 executable,
    for NEWK calculations (to return the fermi energy)
    """

    @classmethod
    def define(cls, spec):
        super(CryNewkCalculation, cls).define(spec)

        spec.input('metadata.options.parser_name', valid_type=str, default='crystal17.newk')

    @classmethod
    def validate_parameters(cls, data):
        validate_against_schema(data.get_dict(), 'prop.newk.schema.json')

    def create_input_content(self):
        lines = self.create_newk_lines(self.inputs.parameters.get_dict())
        lines.append('END')
        return '\n'.join(lines)

    def get_retrieve_list(self):
        return [self.metadata.options.stdout_file_name]

    def get_retrieve_temp_list(self):
        return []
