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
import os
import traceback

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers.parser import Parser

from aiida_crystal17 import __version__
from aiida_crystal17.data.gcube import GaussianCube
from aiida_crystal17.parsers.raw.pbs import parse_pbs_stderr
from aiida_crystal17.parsers.raw.properties_stdout import read_properties_stdout


class CryEch3Parser(Parser):
    """Parser class for parsing outputs from CRYSTAL17 ``properties`` ECH3 computation."""

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

        # parse density file(s)
        density_error = None
        charge_cube = None
        spin_cube = None

        if "retrieved_temporary_folder" not in kwargs:
            density_error = self.exit_codes.ERROR_TEMP_FOLDER_MISSING
        else:
            temporary_folder = kwargs["retrieved_temporary_folder"]
            list_of_temp_files = os.listdir(temporary_folder)
            output_charge_fname = self.node.get_option("output_charge_fname")
            output_spin_fname = self.node.get_option("output_spin_fname")

            if output_charge_fname not in list_of_temp_files:
                density_error = self.exit_codes.ERROR_DENSITY_FILE_MISSING
            else:
                try:
                    charge_cube = GaussianCube(
                        os.path.join(temporary_folder, output_charge_fname)
                    )
                except Exception:
                    traceback.print_exc()
                    density_error = self.exit_codes.ERROR_PARSING_DENSITY_FILE
            if output_spin_fname in list_of_temp_files:
                try:
                    spin_cube = GaussianCube(
                        os.path.join(temporary_folder, output_spin_fname)
                    )
                except Exception:
                    traceback.print_exc()
                    density_error = self.exit_codes.ERROR_PARSING_DENSITY_FILE

        stdout_data["parser_version"] = str(__version__)
        stdout_data["parser_class"] = str(self.__class__.__name__)

        # log errors
        errors = stdout_data.get("errors", [])
        parser_errors = stdout_data.get("parser_errors", [])
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
        self.out("results", Dict(dict=stdout_data))
        if charge_cube:
            self.out("charge", charge_cube)
        if spin_cube:
            self.out("spin", spin_cube)

        if pbs_error is not None:
            return pbs_error

        if stdout_error is not None:
            return stdout_error

        if density_error is not None:
            return density_error

        return ExitCode()
