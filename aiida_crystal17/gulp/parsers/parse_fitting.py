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
A parser to read output from a standard CRYSTAL17 run
"""
import json
import traceback

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers.parser import Parser

from aiida_crystal17.gulp.parsers.raw.parse_output_fit import parse_file
from aiida_crystal17.gulp.data.potential import EmpiricalPotential


class GulpFittingParser(Parser):
    """
    Parser class for parsing output of a GULP potential fitting calculation
    """

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.
        """
        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        mainout_file = self.node.get_option('output_main_file_name')
        if mainout_file not in output_folder.list_object_names():
            return self.exit_codes.ERROR_OUTPUT_FILE_MISSING

        # parse the main output file and add nodes
        self.logger.info('parsing main out file')
        with output_folder.open(mainout_file) as handle:
            try:
                result_dict, exit_code = parse_file(handle, parser_class=self.__class__.__name__)
            except Exception:
                traceback.print_exc()
                return self.exit_codes.ERROR_PARSING_STDOUT

        if result_dict['parser_errors']:
            self.logger.warning('the parser raised the following errors:\n{}'.format('\n\t'.join(
                result_dict['parser_errors'])))
        if result_dict['errors']:
            self.logger.warning('the calculation raised the following errors:\n{}'.format('\n\t'.join(
                result_dict['errors'])))

        if 'structure_names.json' in self.node.list_object_names():
            result_dict['config_names'] = json.loads(self.node.get_object_content('structure_names.json'))

        # look a stderr for fortran warnings, etc, e.g. IEEE_INVALID_FLAG IEEE_OVERFLOW_FLAG IEEE_UNDERFLOW_FLAG
        stderr_file = self.node.get_option('output_stderr_file_name')
        if stderr_file in output_folder.list_object_names():
            with output_folder.open(stderr_file) as handle:
                stderr_content = handle.read()
                if stderr_content:
                    self.logger.warning('the calculation stderr file was not empty:')
                    self.logger.warning(stderr_content)
                    result_dict['warnings'].append(stderr_content.strip())

        exit_code_dump = self.extract_from_dump(output_folder)

        self.out('results', Dict(dict=result_dict))

        if exit_code is not None:
            return self.exit_codes[exit_code]
        elif exit_code_dump is not None and not self.node.get_option('allow_create_potential_fail'):
            return self.exit_codes[exit_code_dump]
        return ExitCode()

    def extract_from_dump(self, output_folder):
        """ extract a potential from a dump file:

        we need to invoke the `read_existing` method
        from the corresponding `gulp.potentials` entry point class

        """
        dump_file = self.node.get_option('output_dump_file_name')
        if dump_file not in output_folder.list_object_names():
            self.logger.error('dump file `{}` not present in retrieved folder'.format(dump_file))
            return 'ERROR_CREATING_NEW_POTENTIAL'

        with output_folder.open(dump_file) as handle:
            dump_content = handle.read()
        dump_lines = dump_content.splitlines()

        if 'potential' not in self.node.inputs:
            self.logger.error('the node does not have a `potential` node input')
            return 'ERROR_CREATING_NEW_POTENTIAL'

        try:
            pair_style = self.node.inputs.potential.pair_style
            parser = self.node.inputs.potential.load_pair_style(pair_style)
        except Exception:
            self.logger.error('could not load dump parser:')
            traceback.print_exc()
            return 'ERROR_CREATING_NEW_POTENTIAL'

        try:
            pot_dict = parser().read_exising(dump_lines)
        except Exception:
            self.logger.error('could not parse dump file:')
            traceback.print_exc()
            return 'ERROR_CREATING_NEW_POTENTIAL'

        try:
            pot_data = EmpiricalPotential(pair_style, pot_dict)
        except Exception:
            self.logger.error('could not create new potential:')
            traceback.print_exc()
            return 'ERROR_CREATING_NEW_POTENTIAL'

        self.out('potential', pot_data)

        return None
