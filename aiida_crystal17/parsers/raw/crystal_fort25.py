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
import traceback

import numpy as np

from aiida_crystal17 import __version__
from aiida_crystal17.common.parsing import split_numbers, convert_units

IHFERM_MAP = {
    0: 'closed shell, insulating system',
    1: 'open shell, insulating system',
    2: 'closed shell, conducting system',
    3: 'open shell, conducting system'
}


def parse_crystal_fort25(content):
    """ parse the fort.25 output from CRYSTAL

    Notes
    -----
    File Format:

    ::

        1ST RECORD : -%-,IHFERM,TYPE,NROW,NCOL,DX,DY,COSXY (format : A3,I1,A4,2I5,1P,(3E12.5))
        2ND RECORD : X0,Y0 (format : 1P,6E12.5)
        3RD RECORD : I1,I2,I3,I4,I5,I6 (format : 6I3)
        4TH RECORD
        AND FOLLOWING : ((RDAT(I,J),I=1,NROW),J=1,NCOL) (format : 1P,6E12.5)

        Meaning of the variables:
        1   NROW            1 (DOSS are written one projection at a time)
            NCOL            number of energy points in which the DOS is calculated
            DX              energy increment (hartree)
            DY              not used
            COSXY           Fermi energy (hartree)
        2   X0              energy corresponding to the first point
            Y0              not used
        3   I1              number of the projection;
            I2              number of atomic orbitals of the projection;
            I3,I4,I5,I6     not used
        4   RO(J),J=1,NCOL  DOS: density of states ro(eps(j)) (atomic units).

    """
    system_type = None
    fermi_energy = None
    energy_delta = None
    initial_energy = None
    len_dos = None
    alpha_projections = {}
    beta_projections = {}
    proj_number = 0

    lines = content.splitlines()
    lineno = 0

    while lineno < len(lines):
        line = lines[lineno].strip()

        if line.startswith('-%-'):
            proj_number += 1

            if system_type is None:
                system_type = line[3]
            elif not system_type == line[3]:
                raise IOError('projection {0} has different system type ({1}) to previous ({2})'.format(
                    proj_number, line[3], system_type))

            if not line[4:8] == 'DOSS':
                raise IOError('projection {0} is not of type DOSS'.format(proj_number))

            nrows, ncols, _, denergy, fermi = split_numbers(line[8:])
            # nrows, ncols = (int(nrows), int(ncols))

            if energy_delta is None:
                energy_delta = denergy
            elif not energy_delta == denergy:
                raise IOError('projection {0} has different delta energy ({1}) to previous ({2})'.format(
                    proj_number, denergy, energy_delta))
            if fermi_energy is None:
                fermi_energy = fermi
            elif not fermi_energy == fermi:
                raise IOError('projection {0} has different fermi energy ({1}) to previous ({2})'.format(
                    proj_number, fermi, fermi_energy))

            lineno += 1
            line = lines[lineno].strip()

            ienergy = split_numbers(line)[1]

            if initial_energy is None:
                initial_energy = ienergy
            elif not initial_energy == ienergy:
                raise IOError('projection {0} has different initial energy ({1}) to previous ({2})'.format(
                    proj_number, ienergy, initial_energy))

            lineno += 1
            line = lines[lineno].strip()

            projid, norbitals, _, _, _, _ = [int(i) for i in line.split()]

            lineno += 1
            line = lines[lineno].strip()

            dos = []
            while not line.startswith('-%-'):
                dos += split_numbers(line)
                if lineno + 1 >= len(lines):
                    break
                lineno += 1
                line = lines[lineno].strip()

            if len_dos is None:
                len_dos = len(dos)
            elif not len_dos == len(dos):
                raise IOError('projection {0} has different dos value lengths ({1}) to previous ({2})'.format(
                    proj_number, len(dos), len_dos))

            if projid not in alpha_projections:
                alpha_projections[projid] = {'id': projid, 'norbitals': norbitals, 'dos': dos}
            elif projid in beta_projections:
                raise IOError('three data sets with same projid ({0}) were found'.format(projid))
            else:
                beta_projections[projid] = {'id': projid, 'norbitals': norbitals, 'dos': dos}
        else:
            lineno += 1

    system_type = IHFERM_MAP[int(system_type)]
    fermi_energy = convert_units(float(fermi_energy), 'hartree', 'eV')

    energy_delta = convert_units(float(energy_delta), 'hartree', 'eV')
    initial_energy = convert_units(float(initial_energy), 'hartree', 'eV')
    len_dos = int(len_dos)
    energies = np.linspace(initial_energy, initial_energy + len_dos * energy_delta, len_dos).tolist()

    total_alpha = None
    total_beta = None
    if alpha_projections:
        total_alpha = alpha_projections.pop(max(alpha_projections.keys()))
    if beta_projections:
        total_beta = beta_projections.pop(max(beta_projections.keys()))

    return {
        'units': {
            'conversion': 'CODATA2014',
            'energy': 'eV'
        },
        'energy': energies,
        'system_type': system_type,
        'fermi_energy': fermi_energy,
        'total_alpha': total_alpha,
        'total_beta': total_beta,
        'projections_alpha': list(alpha_projections.values()) if alpha_projections else None,
        'projections_beta': list(beta_projections.values()) if beta_projections else None,
    }


def parse_crystal_fort25_aiida(fileobj, parser_class):
    """ takes the result from `parse_crystal_fort25` and prepares it for AiiDA output"""
    results_data = {
        'parser_version': str(__version__),
        'parser_class': str(parser_class),
        'parser_errors': [],
        'parser_warnings': [],
        'errors': [],
        'warnings': []
    }

    try:
        read_data = parse_crystal_fort25(fileobj.read())
    except IOError as err:
        traceback.print_exc()
        results_data['parser_errors'].append('Error parsing CRYSTAL 17 main output: {0}'.format(err))
        return results_data, None

    results_data['fermi_energy'] = read_data['fermi_energy']
    results_data['energy_units'] = read_data['units']['energy']
    results_data['units_conversion'] = read_data['units']['conversion']
    results_data['system_type'] = read_data['system_type']

    array_data = {}

    array_data['energies'] = read_data['energy']
    results_data['npts'] = len(array_data['energies'])
    results_data['energy_max'] = max(array_data['energies'])
    results_data['energy_min'] = min(array_data['energies'])

    total_alpha = read_data['total_alpha']['dos']
    results_data['norbitals_total'] = read_data['total_alpha']['norbitals']
    if read_data['total_beta'] is not None:
        results_data['spin'] = True
        total_beta = read_data['total_beta']['dos']
        assert len(total_alpha) == len(total_beta)
    else:
        results_data['spin'] = False

    if read_data['projections_alpha'] is not None:
        results_data['norbitals_projections'] = [p['norbitals'] for p in read_data['projections_alpha']]
        projected_alpha = [p['dos'] for p in read_data['projections_alpha']]
    if read_data['projections_beta'] is not None:
        projected_beta = [p['dos'] for p in read_data['projections_beta']]
        assert len(projected_alpha) == len(projected_beta)

    if read_data['total_beta'] is None:
        array_data['total'] = total_alpha
    else:
        array_data['total_alpha'] = total_alpha
        array_data['total_beta'] = total_beta

    if read_data['projections_alpha'] is not None:
        if read_data['projections_beta'] is not None:
            array_data['projections_alpha'] = total_alpha
            array_data['projections_beta'] = total_beta
        else:
            array_data['projections'] = total_alpha

    return results_data, array_data
