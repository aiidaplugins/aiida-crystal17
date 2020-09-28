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
"""A parser to read output from a CRYSTAL17 DOSS run."""
from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers.parser import Parser

from aiida_crystal17 import __version__
from aiida_crystal17.parsers.raw.pbs import parse_pbs_stderr
from aiida_crystal17.parsers.raw.properties_stdout import read_properties_stdout


class CryNewkParser(Parser):
    """Parser class for parsing outputs from CRYSTAL17 ``properties`` NEWK computation."""

    def parse(self, **kwargs):
        """Parse outputs, store results in database."""
        try:
            output_folder = self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        # parse stderr
        pbs_error = None
        sterr_file = self.node.get_option("scheduler_stderr")
        if sterr_file in output_folder.list_object_names():
            with output_folder.open(sterr_file) as fileobj:
                pbs_exit_code = parse_pbs_stderr(fileobj)
            if pbs_exit_code:
                pbs_error = self.exit_codes[pbs_exit_code]

        # parse stdout file
        stdout_error = None
        stdout_data = {}
        stdout_fname = self.node.get_option("stdout_file_name")
        if stdout_fname not in self.retrieved.list_object_names():
            stdout_error = self.exit_codes.ERROR_OUTPUT_FILE_MISSING
        else:
            with output_folder.open(stdout_fname) as handle:
                stdout_data = read_properties_stdout(handle.read())
            stdout_exit_code = stdout_data.pop("exit_code", None)
            if stdout_exit_code:
                stdout_error = self.exit_codes[stdout_exit_code]

        final_data = stdout_data
        final_data.update(
            {
                "parser_version": str(__version__),
                "parser_class": str(self.__class__.__name__),
            }
        )

        # log errors
        errors = final_data.get("errors", [])
        parser_errors = final_data.get("parser_errors", [])
        if parser_errors:
            self.logger.warning(
                "the parser raised the following errors:\n{}".format(
                    "\n\t".join(parser_errors)
                )
            )
        if errors:
            self.logger.warning(
                "the calculation raised the following errors:\n{}".format(
                    "\n\t".join(errors)
                )
            )

        # make output nodes
        self.out("results", Dict(dict=final_data))

        if pbs_error is not None:
            return pbs_error

        if stdout_error is not None:
            return stdout_error

        return ExitCode()
