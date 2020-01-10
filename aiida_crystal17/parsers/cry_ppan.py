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
"""A parser to read output from a CRYSTAL17 properties PPAN run."""
import traceback

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers.parser import Parser

from aiida_crystal17 import __version__
from aiida_crystal17.parsers.raw.properties_stdout import read_properties_stdout
from aiida_crystal17.parsers.raw.crystal_ppan import parse_crystal_ppan
from aiida_crystal17.parsers.raw.pbs import parse_pbs_stderr


class CryPpanParser(Parser):
    """Parser class for parsing outputs from CRYSTAL17 ``properties`` PPAN computation."""

    def parse(self, **kwargs):
        """Parse outputs, store results in database."""
        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        # parse stderr
        pbs_error = None
        sterr_file = self.node.get_option('scheduler_stderr')
        if sterr_file in output_folder.list_object_names():
            with output_folder.open(sterr_file) as fileobj:
                pbs_exit_code = parse_pbs_stderr(fileobj)
            if pbs_exit_code:
                pbs_error = self.exit_codes[pbs_exit_code]

        # parse stdout file
        stdout_error = None
        stdout_data = {}
        stdout_fname = self.node.get_option('stdout_file_name')
        if stdout_fname not in self.retrieved.list_object_names():
            stdout_error = self.exit_codes.ERROR_OUTPUT_FILE_MISSING
        else:
            with output_folder.open(stdout_fname) as handle:
                stdout_data = read_properties_stdout(handle.read())
            stdout_exit_code = stdout_data.pop('exit_code', None)
            if stdout_exit_code:
                stdout_error = self.exit_codes[stdout_exit_code]

        # parse PPAN.dat file
        ppan_error = None
        ppan_data = {}
        output_ppan_fname = self.node.get_option('output_ppan_fname')
        if output_ppan_fname not in output_folder.list_object_names():
            ppan_error = self.exit_codes.ERROR_PPAN_FILE_MISSING
        else:
            try:
                with output_folder.open(output_ppan_fname) as handle:
                    ppan_data = parse_crystal_ppan(handle.read())
            except Exception:
                traceback.print_exc()
                ppan_error = self.exit_codes.ERROR_PARSING_PPAN_FILE

        final_data = self.merge_output_dicts(stdout_data, ppan_data)

        # log errors
        errors = final_data.get('errors', [])
        parser_errors = final_data.get('parser_errors', [])
        if parser_errors:
            self.logger.warning('the parser raised the following errors:\n{}'.format('\n\t'.join(parser_errors)))
        if errors:
            self.logger.warning('the calculation raised the following errors:\n{}'.format('\n\t'.join(errors)))

        # make output nodes
        self.out('results', Dict(dict=final_data))
        # if iso_arrays is not None:
        #     array_data = ArrayData()
        #     for name, array in iso_arrays.items():
        #         array_data.set_array(name, np.array(array))
        #     self.out('arrays', array_data)

        if pbs_error is not None:
            return pbs_error

        if stdout_error is not None:
            return stdout_error

        if ppan_error is not None:
            return ppan_error

        return ExitCode()

    def merge_output_dicts(self, stdout_data, iso_data):
        """Merge the data returned from the stdout file and iso_data file."""
        final_data = {}
        for key in set(list(stdout_data.keys()) + list(iso_data.keys())):
            if key in ['errors', 'warnings', 'parser_errors', 'parser_exceptions']:
                final_data[key] = stdout_data.get(key, []) + iso_data.get(key, [])
            elif key == 'units':
                units = stdout_data.get(key, {})
                units.update(iso_data.get(key, {}))
                final_data[key] = units
            elif key in stdout_data and key in iso_data:
                self.logger.warning('key in stdout_data and iso_data: {}'.format(key))
                final_data[key] = iso_data[key]
            elif key in iso_data:
                final_data[key] = iso_data[key]
            else:
                final_data[key] = stdout_data[key]

        final_data.update({'parser_version': str(__version__), 'parser_class': str(self.__class__.__name__)})
        return final_data
