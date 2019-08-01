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
"""
Plugin to create a CRYSTAL17 output file from a supplied input file.
"""
import six

from aiida.plugins import DataFactory
from aiida_crystal17.calculations.cry_abstract import CryAbstractCalculation


class CryBasicCalculation(CryAbstractCalculation):
    """
    AiiDA calculation plugin to run the runcry17 executable,
    by supplying a normal .d12 input file and (optional) .gui file
    """

    @classmethod
    def define(cls, spec):

        super(CryBasicCalculation, cls).define(spec)

        spec.input('metadata.options.external_file_name', valid_type=six.string_types, default='fort.34')
        # TODO this has to be fort.34 for crystal exec (but not for parser),
        # so maybe should be fixed

        spec.input(
            'input_file', valid_type=DataFactory('singlefile'), required=True, help='the input .d12 file content.')
        spec.input(
            'input_external',
            valid_type=DataFactory('singlefile'),
            required=False,
            help=('optional input fort.34 (gui) file content '
                  '(for use with EXTERNAL keyword).'))

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        local_copy_list = [[
            self.inputs.input_file.uuid, self.inputs.input_file.filename, self.metadata.options.input_file_name
        ]]
        if 'input_external' in self.inputs:
            local_copy_list.append([
                self.inputs.input_external.uuid, self.inputs.input_external.filename,
                self.metadata.options.external_file_name
            ])

        return self.create_calc_info(
            tempfolder,
            local_copy_list=local_copy_list,
            retrieve_list=[self.metadata.options.output_main_file_name, self.metadata.options.external_file_name])
