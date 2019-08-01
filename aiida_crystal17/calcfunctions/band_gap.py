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
from collections import namedtuple
import traceback

import numpy as np

from aiida.orm import ArrayData, Dict, Float, List
from aiida.engine import calcfunction, ExitCode

BandResult = namedtuple('BandResult', ['fermi', 'left_edge', 'right_edge', 'non_zero_fermi'])


def calculate_band_gap(energies, densities, fermi=0, dtol=1e-8, try_fshifts=(), missing_edge=None):
    """calculate the band gap, given an energy vs density plot

    Parameters
    ----------
    energies : list[float]
    densities : list[float]
    fermi : float
    dtol : float
        tolerance for checking if density is zero
    try_fshifts : tuple[float]
        if the density at the fermi energy is non-zero,
        try shifting the fermi energy by these values, until a non-zero density is found.
        Useful for dealing with band edges at the fermi energy
    missing_edge : object
        the value to return if an edge cannot be determind

    Returns
    -------
    BandResult

    """
    energies = np.array(energies, float)
    densities = np.abs(np.array(densities, float))
    if not len(energies) == len(densities):
        raise AssertionError('the energies and densities arrays are of different lengths')
    if not fermi < energies.max():
        raise AssertionError('the energies range does not contain the fermi energy')
    if not fermi > energies.min():
        raise AssertionError('the energies range does not contain the fermi energy')

    # sort energies
    order = np.argsort(energies)
    energies = energies[order]
    densities = densities[order]

    # find index closest to fermi
    fermi_idx = (np.abs(energies - fermi)).argmin()

    # check density isn't non-zero at fermi
    fermi_non_zero = (densities[fermi_idx] > 0 + dtol)

    # if the density at the fermi is non-zero, try shifting the fermi
    # (useful to deal with band edges at the fermi)
    for fshift in try_fshifts:
        if not fermi_non_zero:
            break
        new_index = np.abs(energies - (fermi + fshift)).argmin()
        if densities[new_index] <= 0 + dtol:
            fermi_non_zero = False
            fermi_idx = new_index

    if fermi_non_zero:
        return BandResult(energies[fermi_idx], missing_edge, missing_edge, True)

    # find left edge
    found_left = False
    for left_idx in reversed(range(0, fermi_idx + 1)):
        if densities[left_idx] > 0 + dtol:
            found_left = True
            break

    # find right edge
    found_right = False
    for right_idx in range(fermi_idx, len(densities)):
        if densities[right_idx] > 0 + dtol:
            found_right = True
            break

    return BandResult(energies[fermi_idx], energies[left_idx] if found_left else missing_edge,
                      energies[right_idx] if found_right else missing_edge, False)


@calcfunction
def calcfunction_band_gap(doss_results, doss_array, dtol=None, try_fshifts=None):
    """calculate the band gap, given DoS data computed by CryDossCalculation

    Parameters
    ----------
    doss_array : aiida.orm.ArrayData
    dtol : aiida.orm.Float
        tolerance for checking if density is zero
    try_fshifts : aiida.orm.List
        if the density at the fermi energy is non-zero,
        try shifting the fermi energy by these values, until a non-zero density is found.
        Useful for dealing with band edges at the fermi energy

    """
    if not isinstance(doss_results, Dict):
        return ExitCode(101, 'doss_results is not of type `aiida.orm.Dict`: {}'.format(doss_results))
    if 'fermi_energy' not in doss_results.get_dict():
        return ExitCode(102, '`fermi_energy` not in doss_results')
    if 'energy_units' not in doss_results.get_dict():
        return ExitCode(102, '`energy_units` not in doss_results')
    if not isinstance(doss_array, ArrayData):
        return ExitCode(103, 'doss_array is not of type `aiida.orm.ArrayData`: {}'.format(doss_array))

    kwargs = {'fermi': doss_results.get_dict()['fermi_energy']}

    if dtol is not None:
        if not isinstance(dtol, Float):
            return ExitCode(104, 'dtol is not of type `aiida.orm.Float`: {}'.format(dtol))
        kwargs['dtol'] = dtol.value

    if try_fshifts is not None:
        if not isinstance(try_fshifts, List):
            return ExitCode(105, 'try_fshifts is not of type `aiida.orm.List`: {}'.format(try_fshifts))
        kwargs['try_fshifts'] = try_fshifts.get_list()

    array_names = doss_array.get_arraynames()
    if 'energies' not in array_names:
        return ExitCode(111, 'doss_array does not contain array `energies`: {}'.format(doss_array))
    if 'total' in array_names:
        if 'total_alpha' in array_names and 'total_beta' in array_names:
            return ExitCode(112, ('doss_array does not contains both array `total` and '
                                  '`total_alpha`, `total_beta`: {}'.format(doss_array)))
    elif 'total_alpha' in array_names and 'total_beta' in array_names:
        if 'total' in array_names:
            return ExitCode(112, ('doss_array does not contains both array `total` and '
                                  '`total_alpha`, `total_beta`: {}'.format(doss_array)))
    else:
        return ExitCode(
            113, 'doss_array does not contain array `total` or `total_alpha` and `total_beta`: {}'.format(doss_array))

    if 'total' in array_names:
        calcs = {'total': doss_array.get_array('total')}
    else:
        alpha_density = doss_array.get_array('total_alpha')
        beta_density = doss_array.get_array('total_beta')
        total_density = np.abs(alpha_density) + np.abs(beta_density)
        calcs = {'alpha': alpha_density, 'beta': beta_density, 'total': total_density}

    final_dict = {'energy_units': doss_results.get_dict()['energy_units']}

    for name, density in calcs.items():
        try:
            result = calculate_band_gap(doss_array.get_array('energies'), density, **kwargs)
        except Exception:
            traceback.print_exc()
            return ExitCode(201, 'calculate_band_gap failed')
        if result.non_zero_fermi:
            bandgap = 0.
        elif result.left_edge is None or result.right_edge is None:
            bandgap = None
        else:
            bandgap = result.right_edge - result.left_edge
        final_dict.update({
            name + '_fermi': result.fermi,
            name + '_left_edge': result.left_edge,
            name + '_right_edge': result.right_edge,
            name + '_zero_fermi': not result.non_zero_fermi,
            name + '_bandgap': bandgap
        })

    return {'results': Dict(dict=final_dict)}
