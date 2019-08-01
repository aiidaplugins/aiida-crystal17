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
A parser to read output from a CRYSTAL17 DOSS run
"""
import traceback

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Float, Dict
from aiida.parsers.parser import Parser

from aiida_crystal17.parsers.raw.newk_output import read_newk_content
from aiida_crystal17.parsers.raw.pbs import parse_pbs_stderr


class CryFermiParser(Parser):
    """
    Parser class for parsing (stdout) output of a standard CRYSTAL17 run
    """

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.
        """
        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        sterr_file = self.node.get_option('scheduler_stderr')
        if sterr_file in output_folder.list_object_names():
            with output_folder.open(sterr_file) as fileobj:
                pbs_error = parse_pbs_stderr(fileobj)
            if pbs_error is not None:
                return self.exit_codes[pbs_error]

        output_main_file_name = self.node.get_option('output_main_file_name')
        if output_main_file_name not in output_folder.list_object_names():
            return self.exit_codes.ERROR_OUTPUT_FILE_MISSING

        self.logger.info('parsing file: {}'.format(output_main_file_name))

        try:
            with output_folder.open(output_main_file_name) as handle:
                data = read_newk_content(handle, self.__class__.__name__)
        except Exception:
            traceback.print_exc()
            return self.exit_codes.ERROR_PARSING_STDOUT

        errors = data.get('errors', [])
        parser_errors = data.get('parser_errors', [])
        if parser_errors:
            self.logger.warning('the parser raised the following errors:\n{}'.format('\n\t'.join(parser_errors)))
        if errors:
            self.logger.warning('the calculation raised the following errors:\n{}'.format('\n\t'.join(errors)))

        self.out('results', Dict(dict=data))

        if 'fermi_energy' in data:
            self.out('fermi_energy', Float(data['fermi_energy']))

        if parser_errors:
            return self.exit_codes.ERROR_PARSING_STDOUT
        elif errors:
            return self.exit_codes.ERROR_CRYSTAL_RUN

        return ExitCode()
