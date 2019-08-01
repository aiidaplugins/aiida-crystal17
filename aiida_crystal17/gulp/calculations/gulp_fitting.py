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
""" a calculation plugin to perform fitting of potentials,
given a set of structures and observables
"""
import copy
import json

import six

from aiida.common.utils import classproperty
from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.common.exceptions import InputValidationError
from aiida.engine import CalcJob
from aiida.orm import Dict, StructureData
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.plugins import DataFactory

from aiida_crystal17.validation import load_schema, validate_against_schema
from aiida_crystal17.gulp.parsers.raw.write_input_fitting import create_input_lines


class GulpFittingCalculation(CalcJob):
    """ a calculation plugin to perform fitting of potentials,
    given a set of structures and observables
    """
    _settings_schema = None
    _observable_defaults = {
        'weighting': 100.0,
        'energy_units': 'eV',
        'energy_units_key': 'energy_units',
        'energy_key': 'energy'
    }

    @classproperty
    def settings_schema(cls):
        """ return the settings schema,
        which is loaded from file the first time it is called only"""
        if cls._settings_schema is None:
            cls._settings_schema = load_schema('fitting_settings.schema.json')
        return copy.deepcopy(cls._settings_schema)

    @classmethod
    def validate_settings(cls, dct):
        """validate a settings dictionary

        Parameters
        ----------
        dct : aiida.orm.Dict

        """
        validate_against_schema(dct.get_dict(), cls.settings_schema)

    @classmethod
    def validate_potential(cls, potential):
        assert potential.has_fitting_flags, 'fitting flags should be set for the potential'

    @classmethod
    def define(cls, spec):
        """ define the process specification """
        super(GulpFittingCalculation, cls).define(spec)

        spec.input('metadata.options.input_file_name', valid_type=six.string_types, default='main.gin')
        spec.input('metadata.options.output_main_file_name', valid_type=six.string_types, default='main.gout')
        spec.input('metadata.options.output_stderr_file_name', valid_type=six.string_types, default='main_stderr.txt')
        spec.input('metadata.options.output_dump_file_name', valid_type=six.string_types, default='fitting.grs')
        spec.input('metadata.options.allow_create_potential_fail', valid_type=bool, default=False)
        spec.input('metadata.options.parser_name', valid_type=six.string_types, default='gulp.fitting')

        spec.input(
            'settings',
            valid_type=Dict,
            required=True,
            validator=cls.validate_settings,
            serializer=to_aiida_type,
            help=('Settings for the fitting, '
                  'see `GulpFittingCalculation.settings_schema` for the accepted format'))

        spec.input(
            'potential',
            valid_type=DataFactory('gulp.potential'),
            required=True,
            serializer=to_aiida_type,
            validator=cls.validate_potential,
            help=('a dictionary defining the potential. '
                  'Note this should have been created with fitting flags initialised'))

        spec.input_namespace(
            'structures', valid_type=StructureData, dynamic=True, help='a dict of structures to fit the potential to')

        spec.input_namespace(
            'observables', valid_type=Dict, dynamic=True, help='a dictionary of observables for each structure')

        # TODO review aiidateam/aiida_core#2997, when closed, for exit code formalization

        # Unrecoverable errors: resources like the retrieved folder or its expected contents are missing
        spec.exit_code(
            200, 'ERROR_NO_RETRIEVED_FOLDER', message='The retrieved folder data node could not be accessed.')
        spec.exit_code(210, 'ERROR_OUTPUT_FILE_MISSING', message='the main (stdout) output file was not found')
        spec.exit_code(211, 'ERROR_TEMP_FOLDER_MISSING', message='the temporary retrieved folder was not found')

        # Unrecoverable errors: required retrieved files could not be read, parsed or are otherwise incomplete
        spec.exit_code(
            300, 'ERROR_PARSING_STDOUT', message=('An error was flagged trying to parse the '
                                                  'gulp exec stdout file'))
        spec.exit_code(301, 'ERROR_STDOUT_EMPTY', message=('The stdout file is empty'))
        spec.exit_code(
            310,
            'ERROR_NOT_ENOUGH_OBSERVABLES',
            message=('The number of fitting variables exceeds the number of observables'))
        spec.exit_code(311, 'ERROR_FIT_UNSUCCESFUL', message=('The fit was not successful'))
        spec.exit_code(
            312,
            'ERROR_GULP_UNKNOWN',
            message=('An error was flagged by GULP, which is not accounted for in another exit code'))
        spec.exit_code(
            313, 'ERROR_CREATING_NEW_POTENTIAL', message=('An error occurred trying to create the new potential'))

        # Significant errors but calculation can be used to restart

        spec.output('results', valid_type=Dict, required=True, help='the data extracted from the main output file')
        spec.default_output_node = 'results'

        spec.output(
            'potential',
            valid_type=DataFactory('gulp.potential'),
            required=False,
            help=('a dictionary defining the fitted potential.'))

    def create_observable_map(self, settings):
        observables = settings['observables']
        observable_map = {}
        if 'energy' in observables:
            units = observables['energy'].get('units', self._observable_defaults['energy_units'])
            units_key = observables['energy'].get('units_key', self._observable_defaults['energy_units_key'])
            energy_key = observables['energy'].get('energy_key', self._observable_defaults['energy_key'])
            weighting = observables['energy'].get('weighting', self._observable_defaults['weighting'])
            if units == 'eV':
                key = 'energy ev'
            else:
                key = 'energy ' + units

            def _get_energy(data):
                dct = data.get_dict()
                for key in [units_key, energy_key]:
                    if key not in dct:
                        raise AssertionError("the observable data Pk={0} does not contain a '{1}' key".format(
                            data.id, key))
                if dct[units_key] != units:
                    # TODO units conversion
                    raise AssertionError("'{}' != {}".format(units_key, units))
                return dct[energy_key], weighting

            observable_map[key] = _get_energy

        return observable_map

    def prepare_for_submission(self, tempfolder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: an aiida.common.folders.Folder subclass
                           where the plugin should put all its files.
        """
        settings = {}
        if 'settings' in self.inputs:
            settings = self.inputs.settings.get_dict()

        # validate that the structures and observables have the same keys
        struct_keys = set(self.inputs.structures.keys())
        observe_keys = set(self.inputs.observables.keys())
        if struct_keys != observe_keys:
            raise InputValidationError('The structures and observables do not match: {} != {}'.format(
                struct_keys, observe_keys))

        # validate number of fitting variables vs number of observables
        if len(observe_keys) < self.inputs.potential.number_of_variables:
            raise InputValidationError('The number of observables supplied ({}) '
                                       'is less than the number of variables required to be fit ({})'.format(
                                           len(observe_keys), self.inputs.potential.number_of_variables))

        content_lines, snames = create_input_lines(
            self.inputs.potential,
            self.inputs.structures,
            self.inputs.observables,
            observables=self.create_observable_map(settings),
            delta=settings.get('gradient_delta', None),
            dump_file=self.metadata.options.output_dump_file_name)

        with tempfolder.open(self.metadata.options.input_file_name, 'w') as f:
            f.write(six.ensure_text('\n'.join(content_lines)))

        with tempfolder.open('structure_names.json', 'w') as handle:
            handle.write(six.ensure_text(json.dumps(snames)))

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
        calcinfo.retrieve_list = [
            self.metadata.options.output_main_file_name, self.metadata.options.output_stderr_file_name,
            self.metadata.options.output_dump_file_name
        ]
        calcinfo.retrieve_temporary_list = []

        return calcinfo
