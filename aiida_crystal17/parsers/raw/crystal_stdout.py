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
Basic outline of parsing sections:

::

    <parse_pre_header>
    ***************************
    <parse_calculation_header>
    ***************************
    <parse_geometry_input>
    * GEOMETRY EDITING
    <parse_calculation_setup>
    CRYSTAL - SCF - TYPE OF CALCULATION :
    <parse_scf_section>
    SCF ENDED
    <parse_scf_final_energy>
    OPTOPTOPTOPT
    <parse_optimisation>
    OPT END -
    <parse_band_gaps>
    FINAL OPTIMIZED GEOMETRY
    <parse_final_geometry>
    MULLIKEN POPULATION ANALYSIS
    <parse_mulliken_analysis>

"""
from collections import namedtuple
import copy
from fnmatch import fnmatch
import re
import traceback

from jsonextended import edict
from aiida_crystal17.common.parsing import split_numbers, convert_units

try:
    from distutils.util import strtobool
except ImportError:
    from distutils import strtobool

ParsedSection = namedtuple('ParsedSection', ['next_lineno', 'data', 'parser_error', 'non_terminating_error'])
ParsedSection.__new__.__defaults__ = (None,) * len(ParsedSection._fields)

# a mapping of known error messages to exit codes, in order of importance
KNOWN_ERRORS = (
    ('END OF DATA IN INPUT DECK', 'ERROR_CRYSTAL_INPUT'),
    ('FORMAT ERROR IN INPUT DECK', 'ERROR_CRYSTAL_INPUT'),
    ('GEOMETRY DATA FILE NOT FOUND', 'ERROR_CRYSTAL_INPUT'),
    ('Wavefunction file can not be found', 'ERROR_WAVEFUNCTION_NOT_FOUND'),  # restart error
    ('SCF ENDED - TOO MANY CYCLES', 'UNCONVERGED_SCF'),
    ('SCF FAILED', 'UNCONVERGED_SCF'),  # usually found after: SCF ENDED - TOO MANY CYCLES
    ('GEOMETRY OPTIMIZATION FAILED', 'UNCONVERGED_GEOMETRY'),  # usually because run out of steps
    ('CONVERGENCE TESTS UNSATISFIED', 'UNCONVERGED_GEOMETRY'),  # usually found after: OPT END - FAILED
    ('OPT END - FAILED', 'UNCONVERGED_GEOMETRY'),
    ('BASIS SET LINEARLY DEPENDENT', 'BASIS_SET_LINEARLY_DEPENDENT'),  # occurs during geometry optimisations
    ('SCF abnormal end', 'ERROR_SCF_ABNORMAL_END'),  # catch all error
    ('MPI_Abort', 'ERROR_MPI_ABORT'))


def read_crystal_stdout(content):

    output = {
        'units': {
            'conversion': 'CODATA2014',
            'energy': 'eV',
            'length': 'angstrom',
            'angle': 'degrees'
        },
        'errors': [],
        'warnings': [],
        'parser_errors': [],
        'parser_exceptions': []
    }

    # remove MPI statuses,
    # which can get mixed with the start of the program stdout and corrupt the output
    # TODO: removing these will affect the reporting of line numbers in errors
    regex = re.compile('(\\s*PROCESS\\s*\\d+\\s*OF\\s*\\d+\\s*WORKING\\s*\n)+')
    content = re.sub(regex, '\n', content)
    lines = content.splitlines()

    if not lines:
        output['parser_errors'] += ['the file is empty']
        return assign_exit_code(output)

    # make an initial parse to find all errors/warnings and start lines for sections
    errors, run_warnings, parser_errors, telapse_seconds, start_lines = initial_parse(lines)
    output['errors'] += errors
    output['warnings'] += run_warnings
    output['parser_errors'] += errors
    if telapse_seconds is not None:
        output['execution_time_seconds'] = telapse_seconds

    lineno = 0

    # parse until the program header
    outcome = parse_section(parse_pre_header, lines, lineno, output, 'non_program')
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    # parse the program header section
    outcome = parse_section(parse_calculation_header, lines, lineno, output, 'header')
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    # parse the initial geometry input
    outcome = parse_section(parse_geometry_input, lines, lineno, output, 'geometry_input')
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    # parse the calculation setup and initial geometry
    outcome = parse_section(parse_calculation_setup, lines, lineno, output, None)
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    # parse the initial SCF run
    outcome = parse_section(parse_scf_section, lines, lineno, output, ('initial_scf', 'cycles'))
    if outcome is None or outcome.parser_error is not None:
        return assign_exit_code(output)
    lineno = outcome.next_lineno

    # parse the final energy of the scf run
    outcome = parse_section(parse_scf_final_energy, lines, lineno, output, ('initial_scf', 'final_energy'))
    # Note: we don't abort on error
    if outcome is not None:
        lineno = outcome.next_lineno

    # TODO test these lines aren't in-between initial scf and opt:
    # ("* GEOMETRY EDITING", "CRYSTAL - SCF - TYPE OF CALCULATION :",  "SCF ENDED")
    # Note: in a few runs I observed, scf maxcycle was reached, but then the scf started again!

    # parse the optimisation (if present)
    if 'optimization' in start_lines:

        outcome = parse_section(parse_optimisation, lines, start_lines['optimization'], output, 'optimisation')
        # Note: we don't abort on error
        if outcome is not None:
            lineno = outcome.next_lineno

        if outcome is not None and outcome.parser_error is None:
            # TODO do band gaps only com after optimisation?
            outcome = parse_section(parse_band_gaps, lines, lineno, output, 'band_gaps')
            # Note: we don't abort on error
            if outcome is not None:
                lineno = outcome.next_lineno

    # parse the final optimized geometry (if present)
    if 'final_geometry' in start_lines:
        outcome = parse_section(parse_final_geometry, lines, start_lines['final_geometry'], output, 'final_geometry')
        # Note: we don't abort on error
        if outcome is not None:
            lineno = outcome.next_lineno

    if 'mulliken' in start_lines:
        outcome = parse_section(parse_mulliken_analysis, lines, start_lines['mulliken'], output, 'mulliken')
        # Note: we don't abort on error
        if outcome is not None:
            lineno = outcome.next_lineno

    return assign_exit_code(output)


def parse_section(func, lines, initial_lineno, output, key_name):
    """parse a section of the stdout file

    Parameters
    ----------
    func : callable
        a function that returns a `ParsedSection` object
    lines : list[str]
    initial_lineno : int
    output : dict
        current output from the parser
    key_name : str or list[str] or None
        the key_name of output to assign the data to (if None directly update)

    Returns
    -------
    ParsedSection or None

    """
    try:
        outcome = func(lines, initial_lineno)
    except Exception as err:
        traceback.print_exc()
        output['parser_exceptions'].append(str(err))
        return None
    if outcome.data:
        if key_name is None:
            output.update(outcome.data)
        else:
            suboutput = output
            if isinstance(key_name, (tuple, list)):
                for key in key_name[:-1]:
                    suboutput = suboutput.setdefault(key, {})
                key_name = key_name[-1]
            suboutput[key_name] = outcome.data
    if outcome.non_terminating_error is not None:
        output['errors'].append(outcome.non_terminating_error)
    if outcome.parser_error is not None:
        output['parser_errors'].append(outcome.parser_error)

    return outcome


def assign_exit_code(output):

    exit_code = 0

    if output['errors']:
        exit_code = 'ERROR_CRYSTAL_RUN'
        for known_error_msg, code_name in KNOWN_ERRORS:
            found = False
            for error_msg in output['errors']:
                if known_error_msg in error_msg:
                    found = True
                    break
            if found:
                exit_code = code_name
                break
    elif output['parser_errors']:
        if any(['TESTGEOM  DIRECTIVE' in msg for msg in output['warnings']]):
            exit_code = 'TESTGEOM_DIRECTIVE'
        else:
            exit_code = 'ERROR_PARSING_STDOUT'
    elif output['parser_exceptions']:
        exit_code = 'ERROR_PARSING_STDOUT'

    output['exit_code'] = exit_code
    return output


def initial_parse(lines):
    """ scan the file for errors, and find the final elapsed time value """
    errors = []
    warnings = []
    parser_errors = []
    mpi_abort = False
    telapse_line = None
    start_lines = {}

    second_opt_line = False
    # This is required since output looks like
    # OPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPT

    # STARTING GEOMETRY OPTIMIZATION - INFORMATION ON SCF MOVED TO SCFOUT.LOG
    # GEOMETRY OPTIMIZATION INFORMATION STORED IN OPTINFO.DAT

    # OPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPTOPT

    for lineno, line in enumerate(lines):

        if 'WARNING' in line.upper():
            warnings.append(line.strip())
        elif 'ERROR' in line:
            errors.append(line.strip())
        elif 'SCF abnormal end' in line:  # only present when run using runcry
            errors.append(line.strip())
        elif 'MPI_Abort' in line:
            # only record one mpi_abort event (to not clutter output)
            if not mpi_abort:
                errors.append(line.strip())
                mpi_abort = True
        elif 'CONVERGENCE TESTS UNSATISFIED' in line.upper():
            errors.append(line.strip())
        elif 'Note: The following floating-point exceptions are signalling:' in line:
            warnings.append(line.strip())
        elif 'TELAPSE' in line:
            telapse_line = lineno

        # search for an optimisation
        elif 'OPTOPTOPTOPT' in line:
            if 'optimization' in start_lines:
                if second_opt_line:
                    parser_errors.append('found two lines starting  optimization section: '
                                         '{0} and {1}'.format(start_lines['optimization'], lineno))
                else:
                    second_opt_line = True
            start_lines['optimization'] = lineno
        elif 'CONVERGENCE ON GRADIENTS SATISFIED AFTER THE FIRST OPTIMIZATION CYCLE' in line:
            if 'optimization' in start_lines:
                if second_opt_line:
                    parser_errors.append('found two lines starting optimization section: '
                                         '{0} and {1}'.format(start_lines['optimization'], lineno))
                else:
                    second_opt_line = True
            start_lines['optimization'] = lineno

        # search for mulliken analysis
        elif line.strip().startswith('MULLIKEN POPULATION ANALYSIS'):
            # can have ALPHA+BETA ELECTRONS and ALPHA-BETA ELECTRONS (denoted in line above mulliken_starts)
            start_lines.setdefault('mulliken', []).append(lineno)

        # search for final geometry
        elif 'FINAL OPTIMIZED GEOMETRY' in line:
            if 'final_geometry' in start_lines:
                parser_errors.append("found two lines starting 'FINAL OPTIMIZED GEOMETRY':"
                                     ' {0} and {1}'.format(start_lines['final_geometry'], lineno))
            start_lines['final_geometry'] = lineno

    total_seconds = None
    if telapse_line:
        total_seconds = int(split_numbers(lines[telapse_line].split('TELAPSE')[1])[0])
        # m, s = divmod(total_seconds, 60)
        # h, m = divmod(m, 60)
        # elapsed_time = "%d:%02d:%02d" % (h, m, s)

    return errors, warnings, parser_errors, total_seconds, start_lines


def parse_pre_header(lines, initial_lineno=0):
    """ parse any data before the program header

    note this is only for runs using runcry (not straight from the binary)

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int

    Returns
    -------
    ParsedSection

    """
    lineno = 0
    meta_data = {}
    num_lines = len(lines)
    line = lines[lineno]
    for i, line in enumerate(lines[initial_lineno:]):
        if '************************' in line:
            # found start of crystal binary stdout
            return ParsedSection(lineno, meta_data, None)

        elif fnmatch(line, 'date:*'):
            meta_data['date'] = line.replace('date:', '').strip()

        elif fnmatch(line, 'resources_used.ncpus =*'):
            meta_data['nprocs'] = int(line.replace('resources_used.ncpus =', ''))

        lineno += 1
        if lineno + 1 >= num_lines:
            return ParsedSection(lineno, meta_data, "couldn't find start of program header (denoted *****)")
        line = lines[lineno]

    return ParsedSection(lineno, meta_data, "couldn't find start of program header (denoted *****)")


def parse_calculation_header(lines, initial_lineno):
    """ parse calculation header

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int

    Returns
    -------
    ParsedSection

    """
    data = {}
    for i, line in enumerate(lines[initial_lineno:]):
        if line.strip().startswith('****************') and i != 0:
            return ParsedSection(initial_lineno + i, data, None)
        if re.findall(r'\s\s\s\s\sCRYSTAL\d{2}(.*)\*', line):
            data['crystal_version'] = int(re.findall(r'\s\s\s\s\sCRYSTAL(\d{2})', line)[0])
        if re.findall('public\\s\\:\\s(.+)\\s\\-', line):
            data['crystal_subversion'] = re.findall('public\\s\\:\\s(.+)\\s\\-', line)[0]
    return ParsedSection(initial_lineno + i, data, "couldn't find end of program header")


def parse_geometry_input(lines, initial_lineno):
    """ parse geometry input data

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int

    Returns
    -------
    ParsedSection

    """
    lineno = initial_lineno
    data = {}
    for i, line in enumerate(lines[initial_lineno:]):
        if line.strip().startswith('* GEOMETRY EDITING'):
            return ParsedSection(lineno + i, data, None)
        # TODO parse relevant data
    return ParsedSection(lineno + i, data, "couldn't find end of geometry input (denoted * GEOMETRY EDITING)")


def parse_calculation_setup(lines, initial_lineno):
    """ parse initial setup data (starting after intital geometry input)

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int

    Returns
    -------
    ParsedSection

    """
    data = {'calculation': {'spin': False}, 'initial_geometry': {}}
    end_lineno = None

    for i, line in enumerate(lines[initial_lineno:]):
        curr_lineno = initial_lineno + i
        line = line.strip()
        if line.startswith('CRYSTAL - SCF - TYPE OF CALCULATION :'):
            end_lineno = curr_lineno
            break

        elif line.startswith('TYPE OF CALCULATION :'):
            data['calculation']['type'] = line.replace('TYPE OF CALCULATION :', '').strip().lower()
            if 'HAMILTONIAN' in lines[curr_lineno + 1]:
                regex = r'\(EXCHANGE\)\[CORRELATION\] FUNCTIONAL:\((.*)\)\[(.*)\]'
                string = lines[curr_lineno + 3].strip()
                if re.match(regex, string):
                    data['calculation']['functional'] = {
                        'exchange': re.search(regex, string).group(1),
                        'correlation': re.search(regex, string).group(2)
                    }

        elif 'SPIN POLARIZ' in line:
            data['calculation']['spin'] = True

        parse_geometry_section(data['initial_geometry'], curr_lineno, line, lines)
        parse_symmetry_section(data['initial_geometry'], curr_lineno, line, lines)

    if end_lineno is None:
        return ParsedSection(curr_lineno, data, "couldn't find start of initial scf calculation")

    regexes = {
        'n_atoms': re.compile(r'\sN. OF ATOMS PER CELL\s*(\d*)', re.DOTALL),
        'n_shells': re.compile(r'\sNUMBER OF SHELLS\s*(\d*)', re.DOTALL),
        'n_ao': re.compile(r'\sNUMBER OF AO\s*(\d*)', re.DOTALL),
        'n_electrons': re.compile(r'\sN. OF ELECTRONS PER CELL\s*(\d*)', re.DOTALL),
        'n_core_el': re.compile(r'\sCORE ELECTRONS PER CELL\s*(\d*)', re.DOTALL),
        'n_symops': re.compile(r'\sN. OF SYMMETRY OPERATORS\s*(\d*)', re.DOTALL),
        'n_kpoints_ibz': re.compile(r'\sNUMBER OF K POINTS IN THE IBZ\s*(\d*)', re.DOTALL),
        'n_kpoints_gilat': re.compile(r'\s NUMBER OF K POINTS\(GILAT NET\)\s*(\d*)', re.DOTALL),
    }
    content = '\n'.join(lines[initial_lineno:end_lineno])
    for name, regex in regexes.items():
        num = regex.search(content)
        if num is not None:
            data['calculation'][name] = int(num.groups()[0])

    return ParsedSection(curr_lineno, data, None)


def parse_geometry_section(data, initial_lineno, line, lines):
    """ parse a section of geometry related variables

    Parameters
    ----------
    data: dict
        existing data to add the geometry data to
    initial_lineno: int
    line: str
        the current line
    lines: list[str]

    Notes
    -----

    For initial and 'FINAL OPTIMIZED GEOMETRY' only::

        DIRECT LATTICE VECTORS CARTESIAN COMPONENTS (ANGSTROM)
                X                    Y                    Z
        0.355114561000E+01   0.000000000000E+00   0.000000000000E+00
        0.000000000000E+00   0.355114561000E+01   0.000000000000E+00
        0.000000000000E+00   0.000000000000E+00   0.535521437000E+01


        CARTESIAN COORDINATES - PRIMITIVE CELL
        *******************************************************************************
        *      ATOM          X(ANGSTROM)         Y(ANGSTROM)         Z(ANGSTROM)
        *******************************************************************************
            1    26 FE    0.000000000000E+00  0.000000000000E+00  0.000000000000E+00
            2    26 FE    1.775572805000E+00  1.775572805000E+00  0.000000000000E+00
            3    16 S    -1.110223024625E-16  1.775572805000E+00  1.393426779074E+00
            4    16 S     1.775572805000E+00  7.885127240037E-16 -1.393426779074E+00

    For initial, final and optimisation steps:

    Primitive cell::

        PRIMITIVE CELL - CENTRING CODE 1/0 VOLUME=    36.099581 - DENSITY  6.801 g/cm^3
                A              B              C           ALPHA      BETA       GAMMA
            2.94439264     2.94439264     4.16400000    90.000000  90.000000  90.000000
        *******************************************************************************
        ATOMS IN THE ASYMMETRIC UNIT    4 - ATOMS IN THE UNIT CELL:    4
            ATOM                 X/A                 Y/B                 Z/C
        *******************************************************************************
            1 T  28 NI    0.000000000000E+00  0.000000000000E+00  0.000000000000E+00

    Crystallographic cell (only if the geometry is not originally primitive)::

        CRYSTALLOGRAPHIC CELL (VOLUME=         74.61846100)
                A              B              C           ALPHA      BETA       GAMMA
            4.21000000     4.21000000     4.21000000    90.000000  90.000000  90.000000

        COORDINATES IN THE CRYSTALLOGRAPHIC CELL
            ATOM                 X/A                 Y/B                 Z/C
        *******************************************************************************
            1 T  12 MG    0.000000000000E+00  0.000000000000E+00  0.000000000000E+00

    """

    # check that units are correct (probably not needed)
    if fnmatch(line, 'LATTICE PARAMETERS*(*)'):
        if not ('ANGSTROM' in line and 'DEGREES' in line):
            raise IOError('was expecting lattice parameters in angstroms and degrees on line:'
                          ' {0}, got: {1}'.format(initial_lineno, line))
        return

    for pattern, field, pattern2 in [('PRIMITIVE*CELL*', 'primitive_cell', 'ATOMS IN THE ASYMMETRIC UNIT*'),
                                     ('CRYSTALLOGRAPHIC*CELL*', 'crystallographic_cell',
                                      'COORDINATES IN THE CRYSTALLOGRAPHIC CELL')]:
        if fnmatch(line, pattern):
            if not fnmatch(lines[initial_lineno + 1].strip(), 'A*B*C*ALPHA*BETA*GAMMA'):
                raise IOError('was expecting A B C ALPHA BETA GAMMA on line:'
                              ' {0}, got: {1}'.format(initial_lineno + 1, lines[initial_lineno + 1]))
            data[field] = edict.merge([
                data.get(field, {}),
                {
                    'cell_parameters':
                    dict(zip(['a', 'b', 'c', 'alpha', 'beta', 'gamma'], split_numbers(lines[initial_lineno + 2])))
                }
            ])
        elif fnmatch(line, pattern2):
            periodic = [True, True, True]
            if not fnmatch(lines[initial_lineno + 1].strip(), 'ATOM*X/A*Y/B*Z/C'):
                # for 2d (slab) can get z in angstrom (and similar for 1d)
                if fnmatch(lines[initial_lineno + 1].strip(), 'ATOM*X/A*Y/B*Z(ANGSTROM)*'):
                    periodic = [True, True, False]
                elif fnmatch(lines[initial_lineno + 1].strip(), 'ATOM*X/A*Y(ANGSTROM)*Z(ANGSTROM)*'):
                    periodic = [True, False, False]
                elif fnmatch(lines[initial_lineno + 1].strip(), 'ATOM*X(ANGSTROM)*Y(ANGSTROM)*Z(ANGSTROM)*'):
                    periodic = [False, False, False]
                    cell_params = dict(
                        zip(['a', 'b', 'c', 'alpha', 'beta', 'gamma'], [500., 500., 500., 90., 90., 90.]))
                    data[field] = edict.merge([data.get(field, {}), {'cell_parameters': cell_params}])
                else:
                    raise IOError('was expecting ATOM X Y Z (in units of ANGSTROM or fractional) on line:'
                                  ' {0}, got: {1}'.format(initial_lineno + 1, lines[initial_lineno + 1]))
            if not all(periodic) and 'cell_parameters' not in data.get(field, {}):
                raise IOError('require cell parameters to have been set for non-periodic directions in line'
                              ' #{0} : {1}'.format(initial_lineno + 1, lines[initial_lineno + 1]))
            a, b, c, alpha, beta, gamma = [None] * 6
            if not all(periodic):
                cell = data[field]['cell_parameters']
                a, b, c, alpha, beta, gamma = [cell[p] for p in ['a', 'b', 'c', 'alpha', 'beta', 'gamma']]

            curr_lineno = initial_lineno + 3
            atom_data = {'ids': [], 'assymetric': [], 'atomic_numbers': [], 'symbols': [], 'fcoords': []}
            atom_data['pbc'] = periodic
            while lines[curr_lineno].strip() and not lines[curr_lineno].strip()[0].isalpha():
                fields = lines[curr_lineno].strip().split()
                atom_data['ids'].append(fields[0])
                atom_data['assymetric'].append(bool(strtobool(fields[1])))
                atom_data['atomic_numbers'].append(int(fields[2]))
                atom_data['symbols'].append(fields[3].lower().capitalize())
                if all(periodic):
                    atom_data['fcoords'].append([float(fields[4]), float(fields[5]), float(fields[6])])
                elif periodic == [True, True, False] and alpha == 90 and beta == 90:
                    atom_data['fcoords'].append([float(fields[4]), float(fields[5]), float(fields[6]) / c])
                # TODO other periodic types (1D, 0D)
                curr_lineno += 1

            if not atom_data['fcoords']:
                atom_data.pop('fcoords')
            data[field] = edict.merge([data.get(field, {}), atom_data])

    # TODO These coordinates are present in initial and final optimized sections,
    # but DON'T work with lattice parameters
    if fnmatch(line, 'CARTESIAN COORDINATES - PRIMITIVE CELL*'):
        if not fnmatch(lines[initial_lineno + 2].strip(), '*ATOM*X(ANGSTROM)*Y(ANGSTROM)*Z(ANGSTROM)'):
            raise IOError('was expecting ATOM X(ANGSTROM) Y(ANGSTROM) Z(ANGSTROM) on line:'
                          ' {0}, got: {1}'.format(initial_lineno + 2, lines[initial_lineno + 2]))

        curr_lineno = initial_lineno + 4
        atom_data = {'ids': [], 'atomic_numbers': [], 'symbols': [], 'ccoords': []}
        while lines[curr_lineno].strip() and not lines[curr_lineno].strip()[0].isalpha():
            fields = lines[curr_lineno].strip().split()
            atom_data['ids'].append(fields[0])
            atom_data['atomic_numbers'].append(int(fields[1]))
            atom_data['symbols'].append(fields[2].lower().capitalize())
            atom_data['ccoords'].append([float(fields[3]), float(fields[4]), float(fields[5])])
            curr_lineno += 1
        data['primitive_cell'] = edict.merge([data.get('primitive_cell', {}), atom_data])

    elif fnmatch(line, 'DIRECT LATTICE VECTORS CARTESIAN COMPONENTS*'):
        if 'ANGSTROM' not in line:
            raise IOError('was expecting lattice vectors in angstroms on line:'
                          ' {0}, got: {1}'.format(initial_lineno, line))
        if not fnmatch(lines[initial_lineno + 1].strip(), 'X*Y*Z'):
            raise IOError('was expecting X Y Z on line:'
                          ' {0}, got: {1}'.format(initial_lineno + 1, lines[initial_lineno + 1]))
        if 'crystallographic_cell' not in data:
            data['crystallographic_cell'] = {}
        if 'cell_vectors' in data['crystallographic_cell']:
            raise IOError('found multiple cell vectors on line:'
                          ' {0}, got: {1}'.format(initial_lineno + 1, lines[initial_lineno + 1]))
        vectors = {
            'a': split_numbers(lines[initial_lineno + 2]),
            'b': split_numbers(lines[initial_lineno + 3]),
            'c': split_numbers(lines[initial_lineno + 4])
        }

        data['primitive_cell']['cell_vectors'] = vectors


def parse_symmetry_section(data, initial_lineno, line, lines):
    """ update dict with symmetry related variables

    Parameters
    ----------
    data: dict
        existing data to add the geometry data to
    initial_lineno: int
    line: str
        the current line
    lines: list[str]

    """
    if fnmatch(line, '*SYMMOPS - TRANSLATORS IN FRACTIONAL UNITS*'):
        nums = split_numbers(line)
        if not len(nums) == 1:
            raise IOError('was expecting a single number, representing the number of symmops, on this line:'
                          ' {0}, got: {1}'.format(initial_lineno, line))
        nsymmops = int(nums[0])
        if not fnmatch(lines[initial_lineno + 1], '*MATRICES AND TRANSLATORS IN THE CRYSTALLOGRAPHIC REFERENCE FRAME*'):
            raise IOError('was expecting CRYSTALLOGRAPHIC REFERENCE FRAME on this line'
                          ' {0}, got: {1}'.format(initial_lineno + 1, lines[initial_lineno + 1].strip()))
        if not fnmatch(lines[initial_lineno + 2], '*V*INV*ROTATION MATRICES*TRANSLATORS*'):
            raise IOError('was expecting symmetry headers on this line'
                          ' {0}, got: {1}'.format(initial_lineno + 2, lines[initial_lineno + 2].strip()))
        symmops = []
        for j in range(nsymmops):
            values = split_numbers(lines[initial_lineno + 3 + j])
            if not len(values) == 14:
                raise IOError('was expecting 14 values for symmetry data on this line'
                              ' {0}, got: {1}'.format(initial_lineno + 3 + j, lines[initial_lineno + 3 + j].strip()))
            symmops.append(values[2:14])
        data['primitive_symmops'] = symmops


def parse_scf_section(lines, initial_lineno, final_lineno=None):
    """ read scf data

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int
    final_lineno: int or None

    Returns
    -------
    ParsedSection

    """
    scf = []
    scf_cyc = None
    last_cyc_num = None
    for k, line in enumerate(lines[initial_lineno:]):
        curr_lineno = k + initial_lineno

        if 'SCF ENDED' in line or (final_lineno is not None and curr_lineno == final_lineno):
            # add last scf cycle
            if scf_cyc:
                scf.append(scf_cyc)
            if 'CONVERGE' not in line:
                return ParsedSection(curr_lineno, scf, None, line.strip())
            else:
                return ParsedSection(curr_lineno, scf, None)

        line = line.strip()

        if fnmatch(line, 'CYC*'):

            # start new cycle
            if scf_cyc is not None:
                scf.append(scf_cyc)
            scf_cyc = {}

            # check we are adding them in sequential order
            cur_cyc_num = split_numbers(line)[0]
            if last_cyc_num is not None:
                if cur_cyc_num != last_cyc_num + 1:
                    return ParsedSection(
                        curr_lineno, scf, 'was expecting the SCF cyle number to be {0} in line {1}: {2}'.format(
                            int(last_cyc_num + 1), curr_lineno, line))
            last_cyc_num = cur_cyc_num

            if fnmatch(line, '*ETOT*'):
                if not fnmatch(line, '*ETOT(AU)*'):
                    raise IOError('was expecting units in a.u. on line {0}, ' 'got: {1}'.format(curr_lineno, line))
                # this is the initial energy of the configuration and so actually the energy of the previous run
                if scf:
                    scf[-1]['energy'] = scf[-1].get('energy', {})
                    scf[-1]['energy']['total'] = convert_units(split_numbers(line)[1], 'hartree', 'eV')

        elif scf_cyc is None:
            continue

        # The total magnetization is the integral of the magnetization in the cell:
        #     MT=∫ (nup-ndown) d3 r
        #
        # The absolute magnetization is the integral of the absolute value of the magnetization in the cell:
        #     MA=∫ |nup-ndown| d3 r
        #
        # In a simple ferromagnetic material they should be equal (except possibly for an overall sign).
        # In simple antiferromagnets (like FeO) MT is zero and MA is twice the magnetization of each of the two atoms.

        if line.startswith('CHARGE NORMALIZATION FACTOR'):
            scf_cyc['CHARGE NORMALIZATION FACTOR'.lower().replace(' ', '_')] = split_numbers(line)[0]
        if line.startswith('SUMMED SPIN DENSITY'):
            scf_cyc['spin_density_total'] = split_numbers(line)[0]

        if line.startswith('TOTAL ATOMIC CHARGES'):
            scf_cyc['atomic_charges_peratom'] = []
            j = curr_lineno + 1
            while len(lines[j].strip().split()) == len(split_numbers(lines[j])):
                scf_cyc['atomic_charges_peratom'] += split_numbers(lines[j])
                j += 1
        if line.startswith('TOTAL ATOMIC SPINS'):
            scf_cyc['spin_density_peratom'] = []
            j = curr_lineno + 1
            while len(lines[j].strip().split()) == len(split_numbers(lines[j])):
                scf_cyc['spin_density_peratom'] += split_numbers(lines[j])
                j += 1
            scf_cyc['spin_density_absolute'] = sum([abs(s) for s in split_numbers(lines[curr_lineno + 1])])

    # add last scf cycle
    if scf_cyc:
        scf.append(scf_cyc)

    return ParsedSection(curr_lineno, scf,
                         'Did not find end of SCF section (starting on line {})'.format(initial_lineno))


def parse_scf_final_energy(lines, initial_lineno, final_lineno=None):
    """ read post initial scf data

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int

    Returns
    -------

    """
    scf_energy = {}
    for i, line in enumerate(lines[initial_lineno:]):
        if final_lineno is not None and i + initial_lineno == final_lineno:
            return ParsedSection(final_lineno, scf_energy)
        if line.strip().startswith('TTTTTTT') or line.strip().startswith('******'):
            return ParsedSection(final_lineno, scf_energy)
        if fnmatch(line.strip(), 'TOTAL ENERGY*DE*'):
            if not fnmatch(line.strip(), 'TOTAL ENERGY*AU*DE*'):
                raise IOError('was expecting units in a.u. on line:' ' {0}, got: {1}'.format(initial_lineno + i, line))
            if 'total_corrected' in scf_energy:
                raise IOError('total corrected energy found twice, on line:'
                              ' {0}, got: {1}'.format(initial_lineno + i, line))
            scf_energy['total_corrected'] = convert_units(split_numbers(line)[1], 'hartree', 'eV')

    return ParsedSection(final_lineno, scf_energy,
                         'Did not find end of Post SCF section (starting on line {})'.format(initial_lineno))


def parse_optimisation(lines, initial_lineno):
    """ read geometric optimisation

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int

    Returns
    -------
    ParsedSection

    """
    if 'CONVERGENCE ON GRADIENTS SATISFIED AFTER THE FIRST OPTIMIZATION CYCLE' in lines[initial_lineno]:
        for k, line in enumerate(lines[initial_lineno:]):
            curr_lineno = initial_lineno + k
            line = line.strip()

            if 'OPT END -' in line:

                if not fnmatch(line, '*E(AU)*'):
                    raise IOError('was expecting units in a.u. on line:' ' {0}, got: {1}'.format(curr_lineno, line))
                data = [{'energy': {'total_corrected': convert_units(split_numbers(lines[-1])[0], 'hartree', 'eV')}}]

                return ParsedSection(curr_lineno, data)

        return ParsedSection(curr_lineno, [],
                             "did not find 'OPT END', after optimisation start at line {}".format(initial_lineno))

    opt_cycles = []
    opt_cyc = None
    scf_start_no = None
    failed_opt_step = False

    for k, line in enumerate(lines[initial_lineno:]):
        curr_lineno = initial_lineno + k
        line = line.strip()

        if 'OPT END -' in line:
            if opt_cyc and not failed_opt_step:
                opt_cycles.append(opt_cyc)
            return ParsedSection(curr_lineno, opt_cycles)

        if fnmatch(line, '*OPTIMIZATION*POINT*'):
            if opt_cyc is not None and not failed_opt_step:
                opt_cycles.append(opt_cyc)
            opt_cyc = {}
            scf_start_no = None
            failed_opt_step = False
        elif opt_cyc is None:
            continue

        # when using ONELOG optimisation key word
        if 'CRYSTAL - SCF - TYPE OF CALCULATION :' in line:
            if scf_start_no is not None:
                return ParsedSection(
                    curr_lineno,
                    opt_cycles, "found two lines starting scf ('CRYSTAL - SCF - ') in opt step {0}:".format(
                        len(opt_cycles)) + ' {0} and {1}'.format(scf_start_no, curr_lineno))
            scf_start_no = curr_lineno
        elif 'SCF ENDED' in line:
            if 'CONVERGE' not in line:
                pass  # errors.append(line.strip())
            outcome = parse_scf_section(lines, scf_start_no + 1, curr_lineno + 1)
            # TODO test if error
            opt_cyc['scf'] = outcome.data

        parse_geometry_section(opt_cyc, curr_lineno, line, lines)

        # TODO move to read_post_scf?
        if fnmatch(line, 'TOTAL ENERGY*DE*'):
            if not fnmatch(line, 'TOTAL ENERGY*AU*DE*AU*'):
                return ParsedSection(curr_lineno, opt_cycles, 'was expecting units in a.u. on line:'
                                     ' {0}, got: {1}'.format(curr_lineno, line))
            opt_cyc['energy'] = opt_cyc.get('energy', {})
            opt_cyc['energy']['total_corrected'] = convert_units(split_numbers(line)[1], 'hartree', 'eV')

        for param in ['MAX GRADIENT', 'RMS GRADIENT', 'MAX DISPLAC', 'RMS DISPLAC']:
            if fnmatch(line, '{}*CONVERGED*'.format(param)):
                if 'convergence' not in opt_cyc:
                    opt_cyc['convergence'] = {}
                opt_cyc['convergence'][param.lower().replace(' ', '_')] = bool(strtobool(line.split()[-1]))

        if fnmatch(line, '*SCF DID NOT CONVERGE. RETRYING WITH A SMALLER OPT STEP*'):
            # TODO add failed optimisation steps with dummy energy and extra parameter?
            # for now discard this optimisation step
            failed_opt_step = True

    if opt_cyc and not failed_opt_step:
        opt_cycles.append(opt_cyc)

    return ParsedSection(curr_lineno, opt_cycles,
                         "did not find 'OPT END', after optimisation start at line {}".format(initial_lineno))


def parse_final_geometry(lines, initial_lineno):
    """ read final optimized geometry section

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int

    Returns
    -------
    ParsedSection

    """
    data = {}
    for i, line in enumerate(lines[initial_lineno:]):
        line = line.strip()
        parse_geometry_section(data, initial_lineno + i, line, lines)
        parse_symmetry_section(data, initial_lineno + i, line, lines)
        # TODO handle exceptions
        # TODO breaking line?

    return ParsedSection(initial_lineno + i, data)


def parse_band_gaps(lines, initial_lineno):
    """ read band gap information

    Note: this is new for CRYSTAL17

    Parameters
    ----------
    lines: list[str]
    initial_lineno: int

    Returns
    -------
    ParsedSection

    """
    band_gaps = {}

    for k, line in enumerate(lines[initial_lineno:]):
        curr_lineno = initial_lineno + k
        line = line.strip()
        # TODO breaking line?
        # TODO use regex:
        # re.compile(r"(DIRECT|INDIRECT) ENERGY BAND GAP:\s*([.\d]*)",
        #            re.DOTALL),
        if 'BAND GAP' in line:
            if fnmatch(line.strip(), 'ALPHA BAND GAP:*eV'):
                bgvalue = split_numbers(line)[0]
                bgtype = 'alpha'
            elif fnmatch(line.strip(), 'BETA BAND GAP:*eV'):
                bgvalue = split_numbers(line)[0]
                bgtype = 'beta'
            elif fnmatch(line.strip(), 'BAND GAP:*eV'):
                bgvalue = split_numbers(line)[0]
                bgtype = 'all'
            else:
                return ParsedSection(initial_lineno, band_gaps,
                                     'found a band gap of unknown format at line {0}: {1}'.format(curr_lineno, line))
            if bgtype in band_gaps:
                return ParsedSection(
                    initial_lineno, band_gaps, 'band gap data already contains {0} value before line {1}: {2}'.format(
                        bgtype, curr_lineno, line))
            band_gaps[bgtype] = bgvalue

    return ParsedSection(initial_lineno, band_gaps)


def parse_mulliken_analysis(lines, mulliken_indices):
    """

    Parameters
    ----------
    lines: list[str]
    mulliken_indices: list[int]

    Returns
    -------
    ParsedSection

    """
    mulliken = {}

    for i, indx in enumerate(mulliken_indices):
        name = lines[indx - 1].strip().lower()
        if not (name == 'ALPHA+BETA ELECTRONS'.lower() or name == 'ALPHA-BETA ELECTRONS'.lower()):
            return ParsedSection(
                mulliken_indices[0], mulliken, 'was expecting mulliken to be alpha+beta or alpha-beta on line:'
                ' {0}, got: {1}'.format(indx - 1, lines[indx - 1]))

        mulliken[name.replace(' ', '_')] = {'ids': [], 'symbols': [], 'atomic_numbers': [], 'charges': []}

        if len(mulliken_indices) > i + 1:
            searchlines = lines[indx + 1:mulliken_indices[i + 1]]
        else:
            searchlines = lines[indx + 1:]
        charge_line = None
        for j, line in enumerate(searchlines):
            if fnmatch(line.strip(), '*ATOM*Z*CHARGE*SHELL*POPULATION*'):
                charge_line = j + 2
                break
        if charge_line is None:
            continue

        while searchlines[charge_line].strip() and not searchlines[charge_line].strip()[0].isalpha():
            fields = searchlines[charge_line].strip().split()
            # shell population can wrap multiple lines, the one we want has the label in it
            if len(fields) != len(split_numbers(searchlines[charge_line])):
                mulliken[name.replace(' ', '_')]['ids'].append(int(fields[0]))
                mulliken[name.replace(' ', '_')]['symbols'].append(fields[1].lower().capitalize())
                mulliken[name.replace(' ', '_')]['atomic_numbers'].append(int(fields[2]))
                mulliken[name.replace(' ', '_')]['charges'].append(float(fields[3]))

            charge_line += 1

    return ParsedSection(mulliken_indices[0], mulliken)


def extract_final_info(parsed_data):
    """extract the final energies and primitive geometry/symmetry
    from the relevant sections of the parse data
    (depending if it was an optimisation or not)
    """
    data = {}
    if 'final_geometry' in parsed_data:
        data = parsed_data['final_geometry']

    if 'primitive_cell' not in data:
        if 'optimisation' in parsed_data:
            data['primitive_cell'] = copy.deepcopy(parsed_data['optimisation'][-1].get('primitive_cell', None))
        elif 'initial_geometry' in parsed_data:
            data['primitive_cell'] = copy.deepcopy(parsed_data['initial_geometry'].get('primitive_cell', None))
        else:
            raise ValueError('no primitive_cell available in parsed data')

    if 'energy' not in data:
        if 'optimisation' in parsed_data:
            energies = parsed_data['optimisation'][-1].get('energy', {})
            if 'total_corrected' not in energies:
                raise ValueError('no optimised energy available in parsed data')
            data['energy'] = energies['total_corrected']
        elif 'initial_scf' in parsed_data:
            energies = parsed_data['initial_scf'].get('final_energy', {})
            if 'total_corrected' not in energies:
                raise ValueError('no scf energy available in parsed data')
            data['energy'] = energies['total_corrected']
        else:
            raise ValueError('no energy available in parsed data')

    if 'primitive_symmops' not in data:
        if 'optimisation' in parsed_data:
            raise ValueError('optimisation, but no primitive_symops specified in final_geometry')
        if 'initial_geometry' in parsed_data and 'primitive_symmops' in parsed_data['initial_geometry']:
            data['primitive_symmops'] = copy.deepcopy(parsed_data['initial_geometry']['primitive_symmops'])
        else:
            raise ValueError('no primitive_symops available in parsed data')

    return data
