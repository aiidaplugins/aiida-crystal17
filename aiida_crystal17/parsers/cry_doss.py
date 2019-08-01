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

import numpy as np

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict, ArrayData
from aiida.parsers.parser import Parser

from aiida_crystal17.parsers.raw.crystal_fort25 import parse_crystal_fort25_aiida
from aiida_crystal17.parsers.raw.pbs import parse_pbs_stderr


class CryDossParser(Parser):
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

        output_isovalue_fname = self.node.get_option('output_isovalue_fname')
        if output_isovalue_fname not in output_folder.list_object_names():
            return self.exit_codes.ERROR_ISOVALUE_FILE_MISSING

        self.logger.info('parsing file: {}'.format(output_isovalue_fname))

        try:
            with output_folder.open(output_isovalue_fname) as handle:
                data, arrays = parse_crystal_fort25_aiida(handle, self.__class__.__name__)
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
        if arrays is not None:
            array_data = ArrayData()
            for name, array in arrays.items():
                array_data.set_array(name, np.array(array))
            self.out('arrays', array_data)

        if parser_errors:
            return self.exit_codes.ERROR_PARSING_STDOUT
        elif errors:
            return self.exit_codes.ERROR_CRYSTAL_RUN

        return ExitCode()
