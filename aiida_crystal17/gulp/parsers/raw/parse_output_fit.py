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
import re

from aiida_crystal17 import __version__

from aiida_crystal17.gulp.parsers.raw.parse_output_common import read_gulp_table


def parse_file(file_obj, parser_class=None):
    """ parse a file resulting from a GULP `fit` run """
    content = file_obj.read()
    lines = content.splitlines()

    lines_length = len(lines)

    output = {
        'parser_version': __version__,
        'parser_class': parser_class,
        'parser_errors': [],
        'parser_warnings': [],
        'warnings': [],
        'errors': []
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

            configs = re.findall('Total number of configurations input =[\\s]+([0-9]+)', line)
            if configs:
                output['total_configurations'] = int(configs[0])
                continue

        if line.strip().startswith('*  General input information'):
            section = 'pre_info'
            continue

        if line.strip().startswith('Start of fitting :'):
            section = 'fitting'
            continue

        if section == 'fitting':
            if line.strip().startswith('Cycle:'):
                output['num_cycles'] = output.get('num_cycles', 0) + 1

        if line.strip().startswith('**** Fit completed successfully ****'):
            output['fit_succeeded'] = True
            section = 'post_info'
            continue

        if line.strip().startswith('**** No lower sum of squares could be found ****'):
            output['errors'].append('**** No lower sum of squares could be found ****')
            output['fit_succeeded'] = False
            section = 'post_info'
            continue

        if line.strip().startswith('**** No. of variables exceeds no. of observables ****'):
            output['errors'].append('**** No. of variables exceeds no. of observables ****')
            output['fit_succeeded'] = False
            section = 'post_info'
            continue

        if line.strip().startswith('Final sum of squares') and not output['fit_succeeded']:
            output['fit_succeeded'] = False
            section = 'post_info'
            continue

        if section == 'post_info':
            try:
                if line.strip().startswith('Final values of parameters'):
                    lineno, output['final_parameters'] = read_gulp_table(
                        lines, lineno, ['parameter', 'original', 'final', 'type'], [int, float, float, assess_species])
                    continue

                if line.strip().startswith('Final values of numerical parameter gradients'):
                    lineno, output['final_gradients'] = read_gulp_table(
                        lines, lineno, ['parameter', 'gradient', 'type'], [int, float, assess_species])
                    continue

                if line.strip().startswith('Final values of residuals'):
                    lineno, output['final_residuals'] = read_gulp_table(
                        lines, lineno, ['observable', 'type', 'value', 'calculated', 'residual', 'error'],
                        [int, str, float, float, float, float])
                    continue

                if line.strip().startswith('Comparison of initial and final observables'):
                    lineno, output['calculated_observables'] = read_gulp_table(
                        lines, lineno, ['observable', 'type', 'value', 'initial', 'final'],
                        [int, str, float, float, float])
                    continue

                if line.strip().startswith('Energy shifts for configurations'):
                    lineno, output['energy_shifts'] = read_gulp_table(
                        lines, lineno, ['configuration', 'energy', 'scale_factor'], [int, float, float])
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

            except IOError as err:
                output['parser_errors'].append(str(err))
                continue

    return output, assign_exit_code(output.get('fit_succeeded', False), output['errors'], output['parser_errors'])


def assess_species(value):
    """ some table finish with 'Parameter Type'  'Species',
    Species can be either:

    - 0 for 'Energy shift'
    - blank (for global variables)
    - <i> <j> for species specific

    """
    # TODO assess_species
    if value.startswith('Energy shift'):
        return value[:12]
    return value


def assign_exit_code(fit_succeeded, gulp_errors, parser_errors):
    """ given the error messages, assign an exit code """
    if '**** No. of variables exceeds no. of observables ****' in gulp_errors:
        return 'ERROR_NOT_ENOUGH_OBSERVABLES'
    elif '**** No lower sum of squares could be found ****' in gulp_errors:
        return 'ERROR_FIT_UNSUCCESFUL'
    elif not fit_succeeded:
        return 'ERROR_FIT_UNSUCCESFUL'
    elif gulp_errors:
        return 'ERROR_GULP_UNKNOWN'
    elif parser_errors:
        return 'ERROR_PARSING_STDOUT'
    return None
