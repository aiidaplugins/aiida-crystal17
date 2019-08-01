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
set unit styles that have a compatibility between LAMMPS
"""


def get_style_map(style):
    """get a map of measurements to units for different LAMMPS styles

    Parameters
    ----------
    style : str
        the LAMMPS style (e.g. 'real' or 'metal')

    Returns
    -------
    dict:
        map of measurement name (e.g. 'mass') to units (e.g. 'grams/mole')

    """
    units_map = {
        'real': {
            'mass': 'grams/mole',
            'distance': 'Angstroms',
            'time': 'femtoseconds',
            'energy': 'Kcal/mole',
            'velocity': 'Angstroms/femtosecond',
            'force': 'Kcal/mole-Angstrom',
            'torque': 'Kcal/mole',
            'temperature': 'Kelvin',
            'pressure': 'atmospheres',
            'dynamic_viscosity': 'Poise',
            'charge': 'e',  # multiple of electron charge (1.0 is a proton)
            'dipole': 'charge*Angstroms',
            'electric field': 'volts/Angstrom',
            'density': 'gram/cm^dim',
        },
        'metal': {
            'mass': 'grams/mole',
            'distance': 'Angstroms',
            'time': 'picoseconds',
            'energy': 'eV',
            'velocity': 'Angstroms/picosecond',
            'force': 'eV/Angstrom',
            'torque': 'eV',
            'temperature': 'Kelvin',
            'pressure': 'bars',
            'dynamic_viscosity': 'Poise',
            'charge': 'e',  # multiple of electron charge (1.0 is a proton)
            'dipole': 'charge*Angstroms',
            'electric field': 'volts/Angstrom',
            'density': 'gram/cm^dim',
        },
        'si': {
            'mass': 'kilograms',
            'distance': 'meters',
            'time': 'seconds',
            'energy': 'Joules',
            'velocity': 'meters/second',
            'force': 'Newtons',
            'torque': 'Newton-meters',
            'temperature': 'Kelvin',
            'pressure': 'Pascals',
            'dynamic_viscosity': 'Pascal*second',
            'charge': 'Coulombs',  # (1.6021765e-19 is a proton)
            'dipole': 'Coulombs*meters',
            'electric field': 'volts/meter',
            'density': 'kilograms/meter^dim',
        },
        'cgs': {
            'mass': 'grams',
            'distance': 'centimeters',
            'time': 'seconds',
            'energy': 'ergs',
            'velocity': 'centimeters/second',
            'force': 'dynes',
            'torque': 'dyne-centimeters',
            'temperature': 'Kelvin',
            'pressure': 'dyne/cm^2',  # or barye': '1.0e-6 bars
            'dynamic_viscosity': 'Poise',
            'charge': 'statcoulombs',  # or esu (4.8032044e-10 is a proton)
            'dipole': 'statcoul-cm',  #: '10^18 debye
            'electric_field': 'statvolt/cm',  # or dyne/esu
            'density': 'grams/cm^dim',
        },
        'electron': {
            'mass': 'amu',
            'distance': 'Bohr',
            'time': 'femtoseconds',
            'energy': 'Hartrees',
            'velocity': 'Bohr/atu',  # [1.03275e-15 seconds]
            'force': 'Hartrees/Bohr',
            'temperature': 'Kelvin',
            'pressure': 'Pascals',
            'charge': 'e',  # multiple of electron charge (1.0 is a proton)
            'dipole_moment': 'Debye',
            'electric_field': 'volts/cm',
        },
        'micro': {
            'mass': 'picograms',
            'distance': 'micrometers',
            'time': 'microseconds',
            'energy': 'picogram-micrometer^2/microsecond^2',
            'velocity': 'micrometers/microsecond',
            'force': 'picogram-micrometer/microsecond^2',
            'torque': 'picogram-micrometer^2/microsecond^2',
            'temperature': 'Kelvin',
            'pressure': 'picogram/(micrometer-microsecond^2)',
            'dynamic_viscosity': 'picogram/(micrometer-microsecond)',
            'charge': 'picocoulombs',  # (1.6021765e-7 is a proton)
            'dipole': 'picocoulomb-micrometer',
            'electric field': 'volt/micrometer',
            'density': 'picograms/micrometer^dim',
        },
        'nano': {
            'mass': 'attograms',
            'distance': 'nanometers',
            'time': 'nanoseconds',
            'energy': 'attogram-nanometer^2/nanosecond^2',
            'velocity': 'nanometers/nanosecond',
            'force': 'attogram-nanometer/nanosecond^2',
            'torque': 'attogram-nanometer^2/nanosecond^2',
            'temperature': 'Kelvin',
            'pressure': 'attogram/(nanometer-nanosecond^2)',
            'dynamic_viscosity': 'attogram/(nanometer-nanosecond)',
            'charge': 'e',  # multiple of electron charge (1.0 is a proton)
            'dipole': 'charge-nanometer',
            'electric_field': 'volt/nanometer',
            'density': 'attograms/nanometer^dim'
        }
    }
    return units_map[style]


def get_pressure(pressure, style):
    # allowed GPa/kPa/MPa/Pa/atm/Nm-2/kbar
    punits = get_style_map(style)['pressure']

    if punits == 'atmospheres':
        return pressure, 'atm'
    elif punits == 'bar':
        return pressure / 1000., 'kbar'
    elif punits == 'Pascals':
        return pressure, 'Pa'
    else:
        raise ValueError('units not allowed: {}'.format(punits))


# def get_energy(energy, style):
#     # allowed eV, kcal, kjmol
#     eunits = _UNITS_DICT[style]['energy']
#
#     if eunits == 'eV':
#         return energy, 'eV'
#     elif eunits == 'Kcal/mole':
#
#     else:
#         raise ValueError('units not allowed: {}'.format(eunits))


def get_units_dict(style, quantities):
    """

    :param style: the unit style set in the lammps input
    :type style: str
    :param quantities: the quantities to get units for
    :type quantities: list
    :return:
    """
    out_dict = {}
    for quantity in quantities:
        units = get_style_map(style)[quantity]
        if units == 'bar':
            units = 'kbar'
        if quantity == 'energy':
            units = 'eV'
        out_dict[quantity + '_units'] = units
    return out_dict
