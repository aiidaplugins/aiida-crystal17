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
Plugin to run GULP
"""
import six

from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.engine import CalcJob
from aiida.plugins import DataFactory


def potential_validator(potential):
    assert not potential.has_fitting_flags, 'fitting flags should not be set for the potential'


class GulpAbstractCalculation(CalcJob):
    """
    AiiDA calculation plugin to run the gulp executable,
    Subclasses must at least implement the
    ``create_input`` and ``get_retrieve_list`` methods,
    and specify a default ``metadata.options.parser_name`` in the spec
    """
    link_output_results = 'results'
    link_output_structure = 'structure'

    @classmethod
    def define(cls, spec):

        super(GulpAbstractCalculation, cls).define(spec)

        spec.input('metadata.options.input_file_name', valid_type=six.string_types, default='main.gin')
        spec.input('metadata.options.output_main_file_name', valid_type=six.string_types, default='main.gout')
        spec.input('metadata.options.output_stderr_file_name', valid_type=six.string_types, default='main_stderr.txt')

        spec.input(
            'structure',
            valid_type=DataFactory('structure'),
            required=True,
            help=('atomic structure used to create the '
                  'geometry section of .gin file content.'))
        spec.input(
            'potential',
            valid_type=DataFactory('gulp.potential'),
            required=True,
            validator=potential_validator,
            help=('parameters to create the '
                  'potential section of the .gin file content.'))
        spec.input(
            'parameters',
            valid_type=DataFactory('dict'),
            required=False,
            help=('additional input parameters '
                  'to create the .gin file content.'))

        # TODO review aiidateam/aiida_core#2997, when closed, for exit code formalization

        # Unrecoverable errors: resources like the retrieved folder or its expected contents are missing
        spec.exit_code(
            200, 'ERROR_NO_RETRIEVED_FOLDER', message='The retrieved folder data node could not be accessed.')
        spec.exit_code(210, 'ERROR_OUTPUT_FILE_MISSING', message='the main output file was not found')

        # Unrecoverable errors: required retrieved files could not be read, parsed or are otherwise incomplete
        spec.exit_code(
            300, 'ERROR_PARSING_STDOUT', message=('An error was flagged trying to parse the '
                                                  'main gulp output file'))
        spec.exit_code(301, 'ERROR_STDOUT_EMPTY', message=('The stdout file is empty'))

        # Significant errors but calculation can be used to restart
        spec.exit_code(
            400, 'ERROR_GULP_UNHANDLED', message='The main gulp output file flagged an error not handled elsewhere')
        spec.exit_code(
            410,
            'ERROR_OPTIMISE_UNSUCCESFUL',
            message='The main gulp output file did not signal that an expected optimisation completed')
        spec.exit_code(
            411,
            'ERROR_OPTIMISE_MAX_ATTEMPTS',
            message='The main gulp output file did not signal that an expected optimisation completed')
        spec.exit_code(
            412,
            'ERROR_OPTIMISE_MAX_CALLS',
            message='The main gulp output file did not signal that an expected optimisation completed')

        spec.output(
            cls.link_output_results,
            valid_type=DataFactory('dict'),
            required=True,
            help='the data extracted from the main output file')
        spec.default_output_node = cls.link_output_results

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """
        content = self.create_input(self.inputs.structure, self.inputs.potential, self.inputs.get('parameters', None),
                                    self.inputs.get('symmetry', None))

        if not isinstance(content, six.text_type):
            content = six.u(content)
        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(content)

        # Prepare CodeInfo object for aiida,
        # describes how a code has to be executed
        code = self.inputs.code
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.stdin_name = self.metadata.options.input_file_name
        codeinfo.stdout_name = self.metadata.options.output_main_file_name
        codeinfo.stderr_name = self.metadata.options.output_stderr_file_name
        codeinfo.withmpi = self.metadata.options.withmpi

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = self.get_retrieve_list()
        calcinfo.retrieve_temporary_list = []

        return calcinfo

    def create_input(self, structure, potential, parameters=None, symmetry=None):
        """ should return the content for main.gin"""
        raise NotImplementedError

    def get_retrieve_list(self):
        """ should return the files to be retrieved """
        return [self.metadata.options.output_main_file_name, self.metadata.options.output_stderr_file_name]
