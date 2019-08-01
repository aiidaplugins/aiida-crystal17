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
import glob
import os
import traceback

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import TrajectoryData
from aiida.parsers.parser import Parser

from aiida_crystal17.parsers.raw.main_out import parse_main_out
from aiida_crystal17.parsers.raw.pbs import parse_pbs_stderr
from aiida_crystal17.parsers.raw.parse_fort34 import parse_fort34
from aiida_crystal17.symmetry import convert_structure


class CryMainParser(Parser):
    """
    Parser class for parsing (stdout) output of a standard CRYSTAL17 run
    """

    def parse(self, retrieved_temporary_folder=None, **kwargs):
        """
        Parse outputs, store results in database.

        Order of error importance:

        - No retrieved folder
        - Scheduler error (e.g. walltime reached)
        - Parsing of stdout file
        - Parsing of temporary folder (i.e. optimisation trajectories)

        """
        try:
            self.retrieved
        except exceptions.NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        # parser scheduler's stderr
        scheduler_exit_code = None
        sterr_file = self.node.get_option('scheduler_stderr')
        if sterr_file in self.retrieved.list_object_names():
            with self.retrieved.open(sterr_file) as fileobj:
                pbs_error = parse_pbs_stderr(fileobj)
            if pbs_error is not None:
                scheduler_exit_code = self.exit_codes[pbs_error]

        # parse temporary folder
        temp_folder_exit_code = self.parse_temporary_folder(retrieved_temporary_folder)

        # parse the stdout file
        stdout_fname = self.node.get_option('output_main_file_name')
        if stdout_fname not in self.retrieved.list_object_names():
            stdout_exit_code = self.exit_codes.ERROR_OUTPUT_FILE_MISSING
        else:
            self.logger.info('parsing stdout file')
            stdout_exit_code = self.parse_stdout(stdout_fname)

        if scheduler_exit_code is not None:
            return scheduler_exit_code
        if stdout_exit_code is not None:
            return stdout_exit_code
        if temp_folder_exit_code is not None:
            return temp_folder_exit_code

        return ExitCode()

    def parse_stdout(self, file_name):
        """parse the main stdout file """
        init_struct = None
        init_settings = None
        if 'structure' in self.node.inputs:
            init_struct = self.node.inputs.structure
        if 'symmetry' in self.node.inputs:
            init_settings = self.node.inputs.symmetry
        with self.retrieved.open(file_name) as fileobj:
            parser_result = parse_main_out(
                fileobj, parser_class=self.__class__.__name__, init_struct=init_struct, init_settings=init_settings)

        for etype in ['errors', 'parser_errors', 'parser_exceptions']:
            errors = parser_result.nodes.results.get_attribute(etype)
            if errors:
                self.logger.warning('the calculation raised the following {0}:\n{1}'.format(etype, '\n\t'.join(errors)))

        # add output nodes
        self.out('results', parser_result.nodes.results)
        if parser_result.nodes.structure is not None:
            self.out('structure', parser_result.nodes.structure)
        if parser_result.nodes.symmetry is not None:
            self.out('symmetry', parser_result.nodes.symmetry)

        return parser_result.exit_code

    def parse_temporary_folder(self, retrieved_temporary_folder):
        """parse the temporary folder """

        if retrieved_temporary_folder is None:
            return None
        if not os.path.exists(retrieved_temporary_folder):
            return self.exit_codes.ERROR_TEMP_FOLDER_MISSING

        # parse optimisation steps
        if 'structure' in self.node.inputs:
            in_symbols = self.node.inputs.structure.get_ase().get_chemical_symbols()

        structures = {}
        for path in glob.iglob(os.path.join(retrieved_temporary_folder, 'opt[ac][0-9][0-9][0-9]')):
            opt_step = int(path[-3:])
            try:
                with open(path) as handle:
                    struct_dict, sym = parse_fort34(handle.readlines())
                    # TODO could also get energy from this file
                structure = convert_structure(struct_dict, 'aiida')
                if 'structure' in self.node.inputs:
                    out_symbols = structure.get_ase().get_chemical_symbols()
                    if out_symbols != in_symbols:
                        raise AssertionError('structure symbols are not compatible: '
                                             '{} != {}'.format(out_symbols, in_symbols))
                    new_structure = self.node.inputs.structure.clone()
                    new_structure.reset_cell(structure.cell)
                    new_structure.reset_sites_positions([s.position for s in structure.sites])
                    structure = new_structure
                structures[opt_step] = structure
            except Exception:
                self.logger.error('error parsing: {}'.format(path))
                traceback.print_exc()
                return self.exit_codes.ERROR_PARSING_OPTIMISATION_GEOMTRIES
        if not structures:
            return None
        sorted_steps = sorted(structures.keys())
        self.logger.debug('optimisations steps found: {}'.format(sorted_steps))
        if sorted_steps != list(range(1, len(sorted_steps) + 1)):
            # this can occur when a step is rejected
            # (e.g. due to an energy change > 0), so shouldn't be raised as error
            pass
        traj_data = TrajectoryData()
        try:
            traj_data.set_structurelist([structures[s] for s in sorted_steps])
        except Exception:
            self.logger.error('an error occurred setting the optimisation trajectory')
            traceback.print_exc()
            return self.exit_codes.ERROR_PARSING_OPTIMISATION_GEOMTRIES
        self.out('optimisation', traj_data)

        return None
