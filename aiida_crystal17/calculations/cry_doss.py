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
import os
import six

from aiida.plugins import DataFactory

from aiida_crystal17.calculations.cry_abstract import CryAbstractCalculation
from aiida_crystal17.parsers.raw.doss_input import create_doss_content
from aiida_crystal17.validation import validate_against_schema


def _validate_inputs(dict_data):
    validate_against_schema(dict_data.get_dict(), 'doss_input.schema.json')


class CryDossCalculation(CryAbstractCalculation):
    """
    AiiDA calculation plugin to run the ``properties`` executable,
    for DOSS calculations.
    """

    @classmethod
    def define(cls, spec):
        super(CryDossCalculation, cls).define(spec)

        spec.input('metadata.options.input_wf_name', valid_type=six.string_types, default='fort.9')
        spec.input('metadata.options.symlink_wf', valid_type=bool, default=False)
        spec.input('metadata.options.output_isovalue_fname', valid_type=six.string_types, default='fort.25')

        spec.input('metadata.options.parser_name', valid_type=six.string_types, default='crystal17.doss')

        spec.input(
            'parameters',
            valid_type=DataFactory('dict'),
            required=True,
            validator=_validate_inputs,
            help='the input parameters to create the DOSS input file.')
        spec.input(
            'wf_folder',
            valid_type=DataFactory('remote'),
            required=True,
            help='the folder containing the wavefunction fort.9 file')

        spec.exit_code(
            352, 'ERROR_ISOVALUE_FILE_MISSING', message='parser could not find the output isovalue (fort.25) file')

        spec.output('results', valid_type=DataFactory('dict'), required=True, help='summary of the parsed data')
        spec.default_output_node = 'results'
        spec.output('arrays', valid_type=DataFactory('array'), required=False, help='energies and DoS arrays')

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """

        input_lines = create_doss_content(self.inputs.parameters.get_dict())
        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(six.ensure_text('\n'.join(input_lines)))

        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(six.ensure_text('\n'.join(input_lines)))

        remote_files = [(self.inputs.wf_folder.computer.uuid,
                         os.path.join(self.inputs.wf_folder.get_remote_path(), self.metadata.options.input_wf_name),
                         'fort.9')]

        return self.create_calc_info(
            tempfolder,
            remote_copy_list=remote_files if not self.metadata.options.symlink_wf else None,
            remote_symlink_list=remote_files if self.metadata.options.symlink_wf else None,
            retrieve_list=[self.metadata.options.output_main_file_name, self.metadata.options.output_isovalue_fname])
