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
import six
from aiida_crystal17.gulp.calculations.gulp_abstract import GulpAbstractCalculation
from aiida_crystal17.gulp.parsers.raw.write_input import InputCreationSingle


class GulpSingleCalculation(GulpAbstractCalculation):
    """
    AiiDA calculation plugin to run the gulp executable,
    for single point energy calculations
    """

    @classmethod
    def define(cls, spec):

        super(GulpSingleCalculation, cls).define(spec)

        spec.input('metadata.options.parser_name', valid_type=six.string_types, default='gulp.single')

    def create_input(self, structure, potential, parameters=None, symmetry=None):
        # TODO assert potential species contains at least one from structure
        input_creation = InputCreationSingle()
        input_creation.create_content(structure, potential.get_input_lines(), parameters, symmetry)
        return input_creation.get_content()
