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
parse the main.gout file of a GULP run and create the required output nodes
"""
import re

from aiida_crystal17 import __version__
from aiida_crystal17.gulp.parsers.raw.parse_output_common import (read_gulp_table, read_energy_components,
                                                                  read_reaxff_econtribs)


def parse_file(file_obj, parser_class=None, single_point_only=False):
    """ parse a file resulting from a GULP single energy or `optimise` run,
    where one structure (configuration) has been supplied
    """
    content = file_obj.read()
    lines = content.splitlines()

    lines_length = len(lines)

    output = {
        'parser_version': __version__,
        'parser_class': parser_class,
        'parser_errors': [],
        'parser_warnings': [],
        'warnings': [],
        'errors': [],
        'energy_units': 'eV'
    }

    if not lines:
        return output, 'ERROR_STDOUT_EMPTY'

    lineno = 0
    section = 'heading'

    while lineno < lines_length:

        line = lines[lineno]
        lineno += 1

        if line.strip().startswith('!! ERROR'):
            output['errors'].append(line.strip())
            continue

        if line.strip().startswith('!! WARNING'):
            output['warnings'].append(line.strip())
            continue

        if section == 'heading':

            version = re.findall('\\* Version = ([0-9]+\\.[0-9]+\\.[0-9]+) \\* Last modified', line)
            if version:
                output['gulp_version'] = version[0]
                continue

            if line.strip().startswith('*  Output for configuration'):
                section = 'output'
                continue

            if lineno >= lines_length:
                output['parser_errors'].append('Reached end of file before finding output section')
                continue

        if section == 'output':

            optimise_start = re.findall('Start of (bulk|surface|polymer) optimisation', line)
            if optimise_start:
                output['opt_type'] = optimise_start[0]
                section = 'optimisation'
                continue

        if section == 'optimisation':

            if line.strip().startswith('**** Optimisation achieved ****'):
                output['opt_succeeded'] = True
                section = 'post_opt'
                continue

            if 'Conditions for a minimum have not been satisfied. However' in line:
                output['opt_succeeded'] = True
                section = 'post_opt'
                output['warnings'].append(('Conditions for a minimum have not been satisfied. '
                                           'However no lower point can be found - treat results with caution'))
                continue

            if 'No variables to optimise - single point performed' in line:
                output['opt_succeeded'] = True
                section = 'post_opt'
                output['warnings'].append('No variables to optimise - single point performed')
                continue

            if '**** Too many failed attempts to optimise ****' in line:
                output['opt_succeeded'] = False
                section = 'post_opt'
                output['errors'].append('**** Too many failed attempts to optimise ****')
                continue

            if '**** Maximum number of function calls has been reached ****' in line:
                output['opt_succeeded'] = False
                section = 'post_opt'
                output['errors'].append('**** Maximum number of function calls has been reached ****')
                continue

            if line.strip().startswith('Final energy'):
                output['opt_succeeded'] = False
                section = 'post_opt'
                output['parser_errors'].append("Reached final energy, before finding 'Optimisation achieved'")
                continue

        if section == 'output':

            if line.strip().startswith('Components of energy :'):
                energy, penergy = (('energy', 'primitive_energy') if single_point_only else
                                   ('initial_energy', 'initial_primitive_energy'))
                try:
                    output[energy], output[penergy], lineno = read_energy_components(lines, lineno)
                except (IOError, ValueError) as err:
                    output['parser_errors'].append(str(err))
                continue

            # TODO convert this to energy if single-point calculation

        if section == 'post_opt':

            if line.strip().startswith('Components of energy :'):
                try:
                    output['final_energy'], output['final_primitive_energy'], lineno = read_energy_components(
                        lines, lineno)
                except (IOError, ValueError) as err:
                    output['parser_errors'].append(str(err))
                continue

        if section == 'output' or section == 'optimisation':
            # will be in 'output' if single energy calculation

            if line.strip().startswith('ReaxFF : Energy contributions:'):
                # TODO these are printed for every optimisation step (if `verbose`), should just find last one then read
                try:
                    output['energy_contributions'], lineno = read_reaxff_econtribs(lines, lineno)
                except (IOError, ValueError) as err:
                    output['parser_errors'].append(str(err))
                continue

        if section == 'output' or section == 'post_opt':
            # will be in 'output' if single energy calculation

            # if line.strip().startswith("Final energy ="):
            #     # this should be the same as the (primitive energy from the components section)
            #     continue

            if line.strip().startswith('Final fractional/Cartesian coordinates of atoms'):
                # output for surfaces and polymers
                try:
                    lineno, output['final_coords'] = read_gulp_table(lines, lineno,
                                                                     ['id', 'label', 'type', 'x', 'y', 'z', 'radius'],
                                                                     [int, str, str, float, float, float, float])
                except (IOError, ValueError) as err:
                    output['parser_errors'].append(str(err))
                continue

            if line.strip().startswith('Final charges from ReaxFF'):
                lineno, output['reaxff_charges'] = read_gulp_table(lines, lineno, ['index', 'atomic_number', 'charge'],
                                                                   [int, int, float])
                continue

            if line.strip().startswith('Time to end of optimisation'):
                # 'Time to end of optimisation =       0.0899 seconds'
                time_match = re.findall('Time to end of optimisation[\\s]*=[\\s]*([+-]?[0-9]*[.]?[0-9]+) seconds', line)
                if time_match:
                    output['opt_time_second'] = float(time_match[0])
                continue

            if line.strip().startswith('Peak dynamic memory used'):
                # 'Peak dynamic memory used =       0.56 MB'
                mem_match = re.findall('Peak dynamic memory used[\\s]*=[\\s]*([+-]?[0-9]*[.]?[0-9]+) MB', line)
                if mem_match:
                    output['peak_dynamic_memory_mb'] = float(mem_match[0])
                continue

            if line.strip().startswith('Total CPU time'):
                # 'Total CPU time  0.0187'
                mem_match = re.findall('Total CPU time[\\s]*([+-]?[0-9]*[.]?[0-9]+)', line)
                if mem_match:
                    output['total_time_second'] = float(mem_match[0])
                continue

    return output, assign_exit_code(
        output.get('opt_succeeded', None), output['errors'], output['parser_errors'], single_point_only)


def assign_exit_code(opt_succeeded, gulp_errors, parser_errors, single_point_only):
    """ given the error messages, assign an exit code """
    if '**** Too many failed attempts to optimise ****' in gulp_errors:
        return 'ERROR_OPTIMISE_MAX_ATTEMPTS'
    elif '**** Maximum number of function calls has been reached ****' in gulp_errors:
        return 'ERROR_OPTIMISE_MAX_CALLS'
    elif opt_succeeded is False and not single_point_only:
        return 'ERROR_OPTIMISE_UNSUCCESFUL'
    elif gulp_errors:
        return 'ERROR_GULP_UNHANDLED'
    elif parser_errors:
        return 'ERROR_PARSING_STDOUT'
    elif opt_succeeded is None and not single_point_only:
        return 'ERROR_GULP_UNHANDLED'
    return None
