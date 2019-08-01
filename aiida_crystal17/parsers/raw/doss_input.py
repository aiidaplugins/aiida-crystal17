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
from aiida_crystal17.validation import validate_against_schema


def read_doss_contents(content):
    """ read the contents of a doss.d3 input file """
    lines = content.splitlines()
    params = {}
    assert lines[0].rstrip() == 'NEWK'
    params['shrink_is'] = int(lines[1].split()[0])
    params['shrink_isp'] = int(lines[1].split()[1])
    assert lines[2].rstrip() == '1 0'
    assert lines[3].rstrip() == 'DOSS'
    settings = lines[4].split()
    assert len(settings) >= 7
    npro = int(settings[0])
    params['npoints'] = int(settings[1])
    band_first = int(settings[2])
    band_last = int(settings[3])
    iplo = int(settings[4])  # noqa: F841
    params['npoly'] = int(settings[5])
    npr = int(settings[6])  # noqa: F841
    if band_first >= 0 and band_last >= 0:
        params['band_minimum'] = band_first
        params['band_maximum'] = band_last
        params['band_units'] = 'bands'
        proj_index = 5
    else:
        params['band_minimum'] = float(lines[5].split()[0])
        params['band_maximum'] = float(lines[5].split()[1])
        params['band_units'] = 'hartree'
        proj_index = 6

    params['atomic_projections'] = []
    params['orbital_projections'] = []

    for line in lines[proj_index:proj_index + npro]:
        values = [int(i) for i in line.split()]
        if values[0] > 0:
            params['orbital_projections'].append(values[1:])
        else:
            params['atomic_projections'].append(values[1:])
    assert lines[proj_index + npro].rstrip() == 'END'

    validate_against_schema(params, 'doss_input.schema.json')

    return params


def create_doss_content(params):
    """create the contents of a doss.d3 input file

    Parameters
    ----------
    params : dict

    Returns
    -------
    list[str]

    Notes
    -----

    NPRO; number of additional (to total) projected densities to calculate (<= 15)
    NPT; number of uniformly spaced energy values (from bottom of band INZB to top of band IFNB)
    INZB; band considered in DOS calculation
    IFNB;  last band considered in DOS calculation
    IPLO; output type (1 = to .d25 file)
    NPOL; number of Legendre polynomials used to expand DOSS (<= 25)
    NPR; number of printing options to switch on

    Unit of measurement:  energy:  hartree; DOSS: state/hartree/cell.

    """
    validate_against_schema(params, 'doss_input.schema.json')

    lines = ['NEWK']
    if not params['shrink_isp'] >= 2 * params['shrink_is']:
        raise AssertionError('ISP<2*IS, low values of the ratio ISP/IS can lead to numerical instabilities.')
    lines.append('{} {}'.format(params['shrink_is'], params['shrink_isp']))
    lines.append('1 0')
    lines.append('DOSS')

    proj_atoms = []
    proj_orbitals = []
    if params.get('atomic_projections', None) is not None:
        proj_atoms = params['atomic_projections']
    if params.get('orbital_projections', None) is not None:
        proj_orbitals = params['orbital_projections']

    npro = len(proj_atoms) + len(proj_orbitals)

    units = params['band_units']

    if units == 'bands':
        inzb = int(params['band_minimum'])
        ifnb = int(params['band_maximum'])
        assert inzb >= 0 and ifnb >= 0
        erange = None
    elif units == 'hartree':
        inzb = ifnb = -1
        bmin = params['band_minimum']
        bmax = params['band_maximum']
        erange = '{} {}'.format(bmin, bmax)
    elif units == 'eV':
        inzb = ifnb = -1
        bmin = params['band_minimum'] / 27.21138602
        bmax = params['band_maximum'] / 27.21138602
        erange = '{0:.8f} {1:.8f}'.format(bmin, bmax)
    else:
        raise ValueError('band_units not recognised: {}'.format(units))

    lines.append('{npro} {npt} {inzb} {ifnb} {iplo} {npol} {npr}'.format(
        npro=npro,
        npt=params.get('npoints', 1000),
        inzb=inzb,
        ifnb=ifnb,
        iplo=1,  # output type (1=fort.25, 2=DOSS.DAT)
        npol=params.get('npoly', 14),
        npr=0,  # number of printing options
    ))
    if erange is not None:
        lines.append(erange)

    if len(proj_atoms) + len(proj_orbitals) > 15:
        raise AssertionError('only 15 projections are allowed per calculation')

    for atoms in proj_atoms:
        lines.append('{} {}'.format(-1 * len(atoms), ' '.join([str(a) for a in atoms])))
    for orbitals in proj_orbitals:
        lines.append('{} {}'.format(len(orbitals), ' '.join([str(o) for o in orbitals])))

    lines.append('END')
    return lines
