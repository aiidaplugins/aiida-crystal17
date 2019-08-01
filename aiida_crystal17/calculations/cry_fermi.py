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

from aiida.common.exceptions import InputValidationError
from aiida.orm import RemoteData, Int, Float, Dict

from aiida_crystal17.calculations.cry_abstract import CryAbstractCalculation


def _validate_shrink(int_data):
    if not int_data.value > 0:
        raise InputValidationError('kpoint must be > 0')


class CryFermiCalculation(CryAbstractCalculation):
    """
    AiiDA calculation plugin to run the runprop17 executable,
    for NEWK calculations (to return the fermi energy)
    """

    @classmethod
    def define(cls, spec):
        super(CryFermiCalculation, cls).define(spec)

        spec.input('metadata.options.input_wf_name', valid_type=six.string_types, default='fort.9')
        spec.input('metadata.options.symlink_wf', valid_type=bool, default=False)

        spec.input('metadata.options.parser_name', valid_type=six.string_types, default='crystal17.fermi')

        spec.input('shrink_is', valid_type=Int, required=True, validator=_validate_shrink)
        spec.input('shrink_isp', valid_type=Int, required=True, validator=_validate_shrink)
        spec.input(
            'wf_folder',
            valid_type=RemoteData,
            required=True,
            help='the folder containing the wavefunction fort.9 file')

        spec.output('fermi_energy', valid_type=Float, required=True, help='The fermi energy (in eV)')
        spec.output('results', valid_type=Dict, required=True, help='result from the parser')
        spec.default_output_node = 'results'

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """

        input_lines = ['NEWK', '{} {}'.format(self.inputs.shrink_is.value, self.inputs.shrink_isp.value), '1 0', 'END']

        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(six.ensure_text('\n'.join(input_lines)))

        remote_files = [(self.inputs.wf_folder.computer.uuid,
                         os.path.join(self.inputs.wf_folder.get_remote_path(), self.metadata.options.input_wf_name),
                         'fort.9')]

        return self.create_calc_info(
            tempfolder,
            remote_copy_list=remote_files if not self.metadata.options.symlink_wf else None,
            remote_symlink_list=remote_files if self.metadata.options.symlink_wf else None,
            retrieve_list=[self.metadata.options.output_main_file_name])
