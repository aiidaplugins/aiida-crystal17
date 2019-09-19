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
"""Common parsing functions for GULP output files."""
import re


def read_gulp_table(lines, lineno, field_names, field_conversions, star_to_none=True):
    """Read tables of the format:

    ::

        --------------------------------------------------------------------------------
            Configuration           Energy (eV)        Scale Factor
        --------------------------------------------------------------------------------
                    1                1.00000                 1.000
                    2                1.00000                 1.000
                    3                1.00000                 1.000
        --------------------------------------------------------------------------------

    Parameters
    ----------
    lines: list[str]
    lineno: int
    field_names: list[str]
    field_conversions: list
        a list of functions for converting each expected field, e.g. [int, float, float]
    star_to_none: bool
        See notes below, if a value has been replaced with `***` then convert it to None

    Returns
    -------
    int: lineno
    values: dict

    Notes
    -----

    Sometimes values can be output as `*`'s (presumably if they are too large)

    ::

            Observable no.  Type            Observable   Calculated    Residual  Error(%)
        --------------------------------------------------------------------------------
                    1        Energy        -90425.39915 ************ ************ -127.948



    """
    if not len(field_names) == len(field_conversions):
        raise AssertionError('the length of field_names ({}) and field_conversions ({}) '
                             'are different'.format(len(field_names), len(field_conversions)))
    num_fields = len(field_conversions)
    start_lineno = lineno
    line = lines[lineno]
    while not line.strip().startswith('---'):
        lineno += 1
        if lineno >= len(lines):
            raise IOError('reached end of file trying to find start of table, '
                          'starting from line #{}'.format(start_lineno))
        line = lines[lineno]

    lineno += 1
    line = lines[lineno]

    while not line.strip().startswith('---'):
        lineno += 1
        if lineno >= len(lines):
            raise IOError('reached end of file trying to find end of table header, '
                          'starting from line #{}'.format(start_lineno))
        line = lines[lineno]

    lineno += 1
    line = lines[lineno]

    values = {f: [] for f in field_names}

    while not line.strip().startswith('---'):
        value_list = line.strip().split(None, num_fields - 1)
        if not len(value_list) == num_fields:
            raise IOError('line #{} did not have at least the expected number of fields ({}): '
                          '{}'.format(lineno, num_fields, value_list))
        try:
            for value, name, convert in zip(value_list, field_names, field_conversions):
                if value.startswith('******') and star_to_none:
                    values[name].append(None)
                else:
                    values[name].append(convert(value))
        except Exception as err:
            raise IOError('line #{} could not be converted to the required format: ' '{}'.format(lineno, err))

        lineno += 1
        if lineno >= len(lines):
            raise IOError('reached end of file trying to find end of table, '
                          'starting from line #{}'.format(start_lineno))
        line = lines[lineno]

    return lineno, values


def read_energy_components(lines, lineno):
    """read the 'components of energy' section of a GULP stdout file

    If a primitive cell is supplied:

    ::

        Components of energy:

        --------------------------------------------------------------------------------
        Interatomic potentials     =          35.51766004 eV
        Monopole - monopole (real) =        -115.57703545 eV
        Monopole - monopole (recip)=        -163.05984388 eV
        Monopole - monopole (total)=        -278.63687932 eV
        --------------------------------------------------------------------------------
        Total lattice energy       =        -243.11921928 eV
        --------------------------------------------------------------------------------
        Total lattice energy       =          -23457.2882 kJ/(mole unit cells)
        --------------------------------------------------------------------------------

    If a non-primitive cell is supplied:

    ::

        --------------------------------------------------------------------------------
        Interatomic potentials     =          59.49169464 eV
        Monopole - monopole (real) =         -65.58576691 eV
        Monopole - monopole (recip)=        -309.07920869 eV
        Monopole - monopole (total)=        -374.66497560 eV
        --------------------------------------------------------------------------------
        Total lattice energy :
            Primitive unit cell      =        -315.17328096 eV
            Non-primitive unit cell  =        -945.51984289 eV
        --------------------------------------------------------------------------------
        Total lattice energy (in kJmol-1):
            Primitive unit cell      =          -30409.4037 kJ/(mole unit cells)
            Non-primitive unit cell  =          -91228.2112 kJ/(mole unit cells)
        --------------------------------------------------------------------------------

    Parameters
    ----------
    lines : list[str]
    lineno : int

    """
    start_lineno = lineno
    line = lines[lineno]
    while not line.strip().startswith('---'):
        lineno += 1
        if lineno >= len(lines):
            raise IOError('reached end of file trying to find start of energy components, '
                          'starting from line {}'.format(start_lineno))
        line = lines[lineno]

    lineno += 1
    line = lines[lineno]

    while not line.strip().startswith('---'):
        # TODO parse this section
        lineno += 1
        if lineno >= len(lines):
            raise IOError('reached end of file trying to find start of total energy section, '
                          'starting from line {}'.format(start_lineno))
        line = lines[lineno]

    lineno += 1
    line = lines[lineno]

    if 'Total lattice energy' not in line:
        raise IOError("Expected line {} to contain 'Total lattice energy': {}".format(lineno, line))

    if '=' in line:
        # structure is primitive
        energy_match = re.findall('Total lattice energy[\\s]*=[\\s]*([^\\s]+) eV', line)
        if not energy_match:
            raise IOError("Expected line {} to match 'Total lattice energy = () eV': {}".format(lineno, line))
        energy = primitive_energy = float(energy_match[0])
    elif ':' in line:
        # structure is non-primitive
        lineno += 1
        line = lines[lineno]
        energy_match = re.findall('Primitive unit cell[\\s]*=[\\s]*([^\\s]+) eV', line)
        if not energy_match:
            raise IOError("Expected line {} to match 'Primitive unit cell = () eV': {}".format(lineno, line))
        primitive_energy = float(energy_match[0])
        lineno += 1
        line = lines[lineno]
        energy_match = re.findall('Non-primitive unit cell[\\s]*=[\\s]*([^\\s]+) eV', line)
        if not energy_match:
            raise IOError("Expected line {} to match 'Non-primitive unit cell = () eV': {}".format(lineno, line))
        energy = float(energy_match[0])
    else:
        raise IOError("Expected line {} to contain 'Total lattice energy = ' or "
                      "'Total lattice energy : ': {}".format(lineno, line))

    return energy, primitive_energy, lineno


def read_reaxff_econtribs(lines, lineno):
    """read the 'ReaxFF : Energy contributions: ' section of a GULP stdout file

    ::

        E(bond)     =     -78.23660866 eV =    -1804.1674905 kcal
        E(bpen)     =       0.00000000 eV =        0.0000000 kcal
        E(lonepair) =       1.21399347 eV =       27.9951750 kcal
        E(over)     =      12.78993990 eV =      294.9411301 kcal
        E(under)    =       0.00000000 eV =        0.0000000 kcal
        E(val)      =      16.66895737 eV =      384.3928245 kcal
        E(pen)      =       0.00000000 eV =        0.0000000 kcal
        E(coa)      =       0.00000000 eV =        0.0000000 kcal
        E(tors)     =       2.35487488 eV =       54.3043568 kcal
        E(conj)     =       0.00000000 eV =        0.0000000 kcal
        E(hb)       =       0.00000000 eV =        0.0000000 kcal
        E(vdw)      =       6.41369507 eV =      147.9023739 kcal
        E(coulomb)  =      -3.34422152 eV =      -77.1190860 kcal
        E(self)     =      -0.10608718 eV =       -2.4464129 kcal

    Parameters
    ----------
    lines : list[str]
    lineno : int
        should be the line below 'ReaxFF : Energy contributions: '

    """
    lineno += 1
    line = lines[lineno]

    energies = {}

    while '=' in line and not line.strip().startswith('**'):

        energy_match = re.findall('E\\((.+)\\)[\\s]*=[\\s]*([^\\s]+) eV', line)
        if not energy_match:
            raise IOError("Expected line {} to start 'E\\((.+)\\)[\\s]*=[\\s]*([^\\s]+) eV': {}".format(lineno, line))
        energies[energy_match[0][0]] = float(energy_match[0][1])

        lineno += 1
        line = lines[lineno]

    return energies, lineno


REAXFF_ENAME_MAP = (
    # original: eb, lammps: c_reax[1], it is assumed this is bond + bpen
    ('bond', 'Bond'),
    ('bpen', 'Bond Penalty'),
    # original: ea, lammps: c_reax[2], it is assumed this is eover + eunder
    ('over', 'Coordination (over)'),
    ('under', 'Coordination (under)'),
    # original: elp, lammps: c_reax[3]
    ('lonepair', 'Lone-Pair'),
    # original: ev, lammps: c_reax[5]
    ('val', 'Valence Angle'),
    # original: epen, lammps: c_reax[6]
    ('pen', 'Valence Angle Penalty'),  # Double-Bond
    # original: ecoa, lammps: c_reax[7]
    ('coa', 'Valence Angle Conjugation'),
    # original: ehb, lammps: c_reax[8]
    ('hb', 'Hydrogen Bond'),
    # original: et, lammps: c_reax[9]
    ('tors', 'Torsional'),
    # original: eco, lammps: c_reax[10]
    ('conj', 'Conjugation'),
    # original: ew, lammps: c_reax[11]
    ('vdw', 'van der Waals'),
    # original: ep, lammps: c_reax[12]
    ('coulomb', 'Coulomb'),
    # original: eqeq, lammps: c_reax[14]
    ('self', 'Charge Equilibration'),
)
