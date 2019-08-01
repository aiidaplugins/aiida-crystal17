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
import traceback

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers.parser import Parser

from aiida_crystal17.gulp.parsers.raw.parse_output_std import parse_file


class GulpSingleParser(Parser):
    """
    Parser class for parsing output of a GULP single point energy calculation
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
                result_dict, exit_code = parse_file(
                    handle, parser_class=self.__class__.__name__, single_point_only=True)
            except Exception:
                traceback.print_exc()
                return self.exit_codes.ERROR_PARSING_STDOUT

        if result_dict['parser_errors']:
            self.logger.warning('the parser raised the following errors:\n{}'.format('\n\t'.join(
                result_dict['parser_errors'])))
        if result_dict['errors']:
            self.logger.warning('the calculation raised the following errors:\n{}'.format('\n\t'.join(
                result_dict['errors'])))

        # look a stderr for fortran warnings, etc,
        # e.g. IEEE_INVALID_FLAG IEEE_OVERFLOW_FLAG IEEE_UNDERFLOW_FLAG
        stderr_file = self.node.get_option('output_stderr_file_name')
        if stderr_file in output_folder.list_object_names():
            with output_folder.open(stderr_file) as handle:
                stderr_content = handle.read()
                if stderr_content:
                    self.logger.warning('the calculation stderr file was not empty:')
                    self.logger.warning(stderr_content)
                    result_dict['warnings'].append(stderr_content.strip())

        self.out('results', Dict(dict=result_dict))

        if exit_code is not None:
            return self.exit_codes[exit_code]
        return ExitCode()
