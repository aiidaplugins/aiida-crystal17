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
import os
import six

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.engine import CalcJob
from aiida.plugins import DataFactory


class CryAbstractCalculation(CalcJob):
    """
    AiiDA calculation plugin to run the runcry17 executable,
    Subclasses must at least specify input nodes,
    and implement a `prepare_for_submission` method
    """
    link_output_results = 'results'
    link_output_structure = 'structure'
    link_output_symmetry = 'symmetry'

    @classmethod
    def define(cls, spec):

        super(CryAbstractCalculation, cls).define(spec)

        spec.input('metadata.options.input_file_name', valid_type=six.string_types, default='INPUT')
        spec.input('metadata.options.output_main_file_name', valid_type=six.string_types, default='main.out')

        spec.input('metadata.options.parser_name', valid_type=six.string_types, default='crystal17.main')

        # TODO review aiidateam/aiida_core#2997, when closed, for exit code formalization

        # Unrecoverable errors: resources like the retrieved folder or its expected contents are missing
        spec.exit_code(
            200, 'ERROR_NO_RETRIEVED_FOLDER', message='The retrieved folder data node could not be accessed.')
        spec.exit_code(210, 'ERROR_OUTPUT_FILE_MISSING', message='the main (stdout) output file was not found')
        spec.exit_code(211, 'ERROR_TEMP_FOLDER_MISSING', message='the temporary retrieved folder was not found')

        # Unrecoverable errors: required retrieved files could not be read, parsed or are otherwise incomplete
        spec.exit_code(
            300,
            'ERROR_PARSING_STDOUT',
            message=('An error was flagged trying to parse the '
                     'crystal exec stdout file'))
        spec.exit_code(  # TODO is this an unrecoverable error?
            301,
            'ERROR_PARSING_OPTIMISATION_GEOMTRIES',
            message=("An error occurred parsing the 'opta'/'optc' geometry files"))
        spec.exit_code(
            302, 'TESTGEOM_DIRECTIVE', message=('The crystal exec stdout file denoted that the run was a testgeom'))

        spec.exit_code(350, 'ERROR_CRYSTAL_INPUT', message='the input file could not be read by CRYSTAL')
        spec.exit_code(
            351, 'ERROR_WAVEFUNCTION_NOT_FOUND', message='CRYSTAL could not find the required wavefunction file')

        # Significant errors but calculation can be used to restart
        spec.exit_code(
            400, 'ERROR_OUT_OF_WALLTIME', message='The calculation stopped prematurely because it ran out of walltime.')
        spec.exit_code(
            401, 'ERROR_OUT_OF_MEMORY', message='The calculation stopped prematurely because it ran out of memory.')
        spec.exit_code(
            402,
            'ERROR_OUT_OF_VMEMORY',
            message='The calculation stopped prematurely because it ran out of virtual memory.')

        spec.exit_code(
            411, 'UNCONVERGED_SCF', message='SCF convergence did not finalise (usually due to reaching step limit)')
        spec.exit_code(
            412,
            'UNCONVERGED_GEOMETRY',
            message='Geometry convergence did not finalise (usually due to reaching step limit)')
        spec.exit_code(
            413, 'BASIS_SET_LINEARLY_DEPENDENT', message='an error encountered usually during geometry optimisation')
        spec.exit_code(414, 'ERROR_SCF_ABNORMAL_END', message='an error was encountered during an SCF computation')
        spec.exit_code(415, 'ERROR_MPI_ABORT', message='an unknown error was encountered, causing the MPI to abort')
        spec.exit_code(499, 'ERROR_CRYSTAL_RUN', message='The main crystal output file flagged an unhandled error')

        # errors in symmetry node consistency checks
        spec.exit_code(510, 'ERROR_SYMMETRY_INCONSISTENCY', message=('inconsistency in the input and output symmetry'))
        spec.exit_code(520, 'ERROR_SYMMETRY_NOT_FOUND', message=('primitive symmops were not found in the output file'))

        spec.output(
            cls.link_output_results,
            valid_type=DataFactory('dict'),
            required=True,
            help='the data extracted from the main output file')
        spec.default_output_node = cls.link_output_results
        spec.output(
            cls.link_output_structure,
            valid_type=DataFactory('structure'),
            required=False,
            help='the structure output from the calculation')
        spec.output(
            cls.link_output_symmetry,
            valid_type=DataFactory('crystal17.symmetry'),
            required=False,
            help='the symmetry data from the calculation')

    def create_calc_info(self,
                         tempfolder,
                         local_copy_list=None,
                         remote_copy_list=None,
                         remote_symlink_list=None,
                         retrieve_list=None,
                         retrieve_temporary_list=None):
        """Prepare CalcInfo object for aiida,
        to describe how the computation will be executed and recovered
        """
        # Prepare CodeInfo object for aiida,
        # describes how a code has to be executed
        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        if self.metadata.options.withmpi:
            # parallel versions of crystal (Pcrystal, Pproperties & MPPcrystal)
            # read data specifically from a file called INPUT
            if self.metadata.options.input_file_name != 'INPUT':
                tempfolder.insert_path(
                    os.path.join(tempfolder.abspath, self.metadata.options.input_file_name),
                    dest_name='INPUT',
                )
        else:
            codeinfo.stdin_name = self.metadata.options.input_file_name
        codeinfo.stdout_name = self.metadata.options.output_main_file_name
        # serial version output to stdout, but parallel version output to stderr!
        # so we join the files
        codeinfo.join_files = True
        codeinfo.cmdline_params = []
        codeinfo.withmpi = self.metadata.options.withmpi

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = local_copy_list or []
        calcinfo.remote_copy_list = remote_copy_list or []
        calcinfo.remote_symlink_list = remote_symlink_list or []
        calcinfo.retrieve_list = retrieve_list or []
        calcinfo.retrieve_temporary_list = retrieve_temporary_list or []

        return calcinfo
