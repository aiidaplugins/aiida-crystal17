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
from aiida.plugins import DataFactory
from aiida_crystal17.gulp.calculations.gulp_abstract import GulpAbstractCalculation
from aiida_crystal17.gulp.parsers.raw.write_input import InputCreationOpt


class GulpOptCalculation(GulpAbstractCalculation):
    """
    AiiDA calculation plugin to run the gulp executable,
    for single point energy calculations
    """

    @classmethod
    def define(cls, spec):

        super(GulpOptCalculation, cls).define(spec)

        spec.input('metadata.options.parser_name', valid_type=six.string_types, default='gulp.optimize')

        spec.input(
            'metadata.options.out_cif_file_name',
            valid_type=six.string_types,
            default='output.cif',
            help='name of the cif file to output with final geometry')
        spec.input(
            'metadata.options.use_input_kinds',
            valid_type=bool,
            default=True,
            help=('if True, use the atoms kinds from the input structure, '
                  'when creating the output structure'))
        # spec.input('metadata.options.out_str_file_name',
        #            valid_type=six.string_types, default='output.str',
        #            help="name of the str file (i.e. a CRYSTAL98 .gui file)")

        spec.input(
            'symmetry',
            valid_type=DataFactory('crystal17.symmetry'),
            required=False,
            help=('parameters to create the symmetry section of the '
                  '.gin file content (for constrained optimisation).'))

        spec.exit_code(250, 'ERROR_CIF_FILE_MISSING', message='the output cif file was not found')
        spec.exit_code(
            251,
            'ERROR_MISSING_INPUT_STRUCTURE',
            message='an input structure is required to create the output structure of an optimisation')
        spec.exit_code(
            252, 'ERROR_CIF_INCONSISTENT', message='the output cif file was not consistent with the input structure')
        spec.exit_code(
            253,
            'ERROR_STRUCTURE_PARSING',
            message='The final structure coordinates were not parsed from the output file')

        spec.output(
            cls.link_output_structure,
            valid_type=DataFactory('structure'),
            required=True,
            help='the optimized structure output from the calculation')

    def create_input(self, structure, potential, parameters=None, symmetry=None):
        input_creation = InputCreationOpt(outputs={'cif': self.metadata.options.out_cif_file_name})
        # TODO assert potential species contains at least one from structure
        input_creation.create_content(structure, potential.get_input_lines(), parameters, symmetry)
        return input_creation.get_content()

    def get_retrieve_list(self):
        """ should return the files to be retrieved """
        return [
            self.metadata.options.output_main_file_name, self.metadata.options.output_stderr_file_name,
            self.metadata.options.out_cif_file_name
        ]
