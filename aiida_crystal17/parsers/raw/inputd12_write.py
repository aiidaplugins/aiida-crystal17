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
module to write CRYSTAL17 .d12 files
"""
import six
from aiida_crystal17.common import get_keys
from aiida_crystal17.validation import validate_against_schema

# TODO check float format and rounding, e.g. "{}".format(0.00001) -> 1e-05, can CRYSTAL handle that?

# TODO SHRINK where IS=0 and IS1 IS2 IS3 given
# TODO FIELD/FIELDCON
# TODO FREQCALC
# TODO ANHARM
# TODO EOS

# TODO RESTART (need to provide files from previous remote folder)

# TODO incompatability tests e.g. using ATOMSPIN without SPIN (and spin value of SPINLOCK)

# TODO look at https://gitlab.com/ase/ase/blob/master/ase/calculators/crystal.py to see if anything can be used


def format_value(dct, keys):
    """return the value + a new line, or empty string if keys not found"""
    value = get_keys(dct, keys, None)
    if value is None:
        return ''
    if isinstance(value, dict):
        outstr = ''
        for keyword in sorted(value.keys()):
            args = value[keyword]
            if isinstance(args, bool):
                if args:
                    outstr += '{}\n'.format(keyword)
            elif isinstance(args, (list, tuple)):
                outstr += '{0}\n{1}\n'.format(keyword, ' '.join([str(a) for a in args]))
            else:
                outstr += '{0}\n{1}\n'.format(keyword, args)
        return outstr

    return '{}\n'.format(value)


def write_input(indict, basis_sets, atom_props=None):
    """write input of a validated input dictionary

    Parameters
    ----------
    indict: dict
        dictionary of inputs
    basis_sets: list
        list of basis set strings or objects with `content` property
    atom_props: dict or None
        atom ids with specific properties;
        "spin_alpha", "spin_beta", "unfixed", "ghosts"

    Returns
    -------
    str

    """
    # validation
    validate_against_schema(indict, 'inputd12.schema.json')
    if not basis_sets:
        raise ValueError('there must be at least one basis set')
    elif not all([isinstance(b, six.string_types) or hasattr(b, 'content') for b in basis_sets]):
        raise ValueError('basis_sets must be either all strings' 'or all objects with a `content` property')
    if atom_props is None:
        atom_props = {}
    if not set(atom_props.keys()).issubset(['spin_alpha', 'spin_beta', 'unfixed', 'ghosts']):
        raise ValueError('atom_props should only contain: ' "'spin_alpha', 'spin_beta', 'unfixed', 'ghosts'")
    # validate that a index isn't in both spin_alpha and spin_beta
    allspin = atom_props.get('spin_alpha', []) + atom_props.get('spin_beta', [])
    if len(set(allspin)) != len(allspin):
        raise ValueError('a kind cannot be in both spin_alpha and spin_beta: {}'.format(allspin))

    outstr = ''

    # Title
    title = get_keys(indict, ['title'], 'CRYSTAL run')
    outstr += '{}\n'.format(' '.join(title.splitlines()))  # must be one line

    outstr = _geometry_block(outstr, indict, atom_props)

    outstr = _basis_set_block(outstr, indict, basis_sets, atom_props)

    outstr = _hamiltonian_block(outstr, indict, atom_props)

    return outstr


def _hamiltonian_block(outstr, indict, atom_props):
    # Hamiltonian Optional Keywords
    outstr += format_value(indict, ['scf', 'single'])
    # DFT Optional Block
    if get_keys(indict, ['scf', 'dft'], False):

        outstr += 'DFT\n'

        xc = get_keys(indict, ['scf', 'dft', 'xc'], raise_error=True)
        if isinstance(xc, (tuple, list)):
            if len(xc) == 2:
                outstr += 'CORRELAT\n'
                outstr += '{}\n'.format(xc[0])
                outstr += 'EXCHANGE\n'
                outstr += '{}\n'.format(xc[1])
        else:
            outstr += format_value(indict, ['scf', 'dft', 'xc'])

        if get_keys(indict, ['scf', 'dft', 'SPIN'], False):
            outstr += 'SPIN\n'

        outstr += format_value(indict, ['scf', 'dft', 'grid'])
        outstr += format_value(indict, ['scf', 'dft', 'grid_weights'])
        outstr += format_value(indict, ['scf', 'dft', 'numerical'])

        outstr += 'END\n'

    # # K-POINTS (SHRINK\nPMN Gilat)
    k_is, k_isp = get_keys(indict, ['scf', 'k_points'], raise_error=True)
    outstr += 'SHRINK\n'
    if isinstance(k_is, int):
        outstr += '{0} {1}\n'.format(k_is, k_isp)
    else:
        outstr += '0 {0}\n'.format(k_isp)
        outstr += '{0} {1} {2}\n'.format(k_is[0], k_is[1], k_is[2])
    # RESTART
    if get_keys(indict, ['scf', 'GUESSP'], False):
        outstr += 'GUESSP\n'
    # ATOMSPIN
    spins = []
    for anum in atom_props.get('spin_alpha', []):
        spins.append((anum, 1))
    for anum in atom_props.get('spin_beta', []):
        spins.append((anum, -1))
    if spins:
        outstr += 'ATOMSPIN\n'
        outstr += '{}\n'.format(len(spins))
        for anum, spin in sorted(spins):
            outstr += '{0} {1}\n'.format(anum, spin)

    # SCF/Other Optional Keywords
    outstr += format_value(indict, ['scf', 'numerical'])
    outstr += format_value(indict, ['scf', 'fock_mixing'])
    outstr += format_value(indict, ['scf', 'spinlock'])
    for keyword in sorted(get_keys(indict, ['scf', 'post_scf'], [])):
        outstr += '{}\n'.format(keyword)

    # Hamiltonian and SCF End
    outstr += 'END\n'
    return outstr


def _geometry_block(outstr, indict, atom_props):
    # Geometry
    outstr += 'EXTERNAL\n'  # we assume external geometry
    # Geometry Optional Keywords (including optimisation)
    for keyword in get_keys(indict, ['geometry', 'info_print'], []):
        outstr += '{}\n'.format(keyword)
    for keyword in get_keys(indict, ['geometry', 'info_external'], []):
        outstr += '{}\n'.format(keyword)
    if indict.get('geometry', {}).get('optimise', False):
        outstr += 'OPTGEOM\n'
        outstr += format_value(indict, ['geometry', 'optimise', 'type'])
        unfixed = atom_props.get('unfixed', [])
        if unfixed:
            outstr += 'FRAGMENT\n'
            outstr += '{}\n'.format(len(unfixed))
            outstr += ' '.join([str(a) for a in sorted(unfixed)]) + '\n'
        outstr += format_value(indict, ['geometry', 'optimise', 'hessian'])
        outstr += format_value(indict, ['geometry', 'optimise', 'gradient'])
        for keyword in sorted(get_keys(indict, ['geometry', 'optimise', 'info_print'], [])):
            outstr += '{}\n'.format(keyword)
        outstr += format_value(indict, ['geometry', 'optimise', 'convergence'])
        outstr += 'ENDOPT\n'

    # Geometry End
    outstr += 'END\n'
    return outstr


def _basis_set_block(outstr, indict, basis_sets, atom_props):
    # Basis Sets
    if isinstance(basis_sets[0], six.string_types):
        outstr += '\n'.join([basis_set.strip() for basis_set in basis_sets])
    else:
        outstr += '\n'.join([basis_set.content.strip() for basis_set in basis_sets])
    outstr += '\n99 0\n'
    # GHOSTS
    ghosts = atom_props.get('ghosts', [])
    if ghosts:
        outstr += 'GHOSTS\n'
        outstr += '{}\n'.format(len(ghosts))
        outstr += ' '.join([str(a) for a in sorted(ghosts)]) + '\n'

    # Basis Sets Optional Keywords
    outstr += format_value(indict, ['basis_set'])
    # Basis Sets End
    outstr += 'END\n'
    return outstr


def create_atom_properties(structure, kinds_data=None):
    """ create dict of properties for each atom

    :param structure: ``StructureData``
    :param kinds_data: ``KindData`` atom kind data for each atom
    :return: dict of atom properties
    :rtype: dict

    """
    if kinds_data is None:
        return {'spin_alpha': [], 'spin_beta': [], 'ghosts': []}

    if set(kinds_data.data.kind_names) != set(structure.get_kind_names()):
        raise AssertionError('kind names are different for structure data and kind data: '
                             '{0} != {1}'.format(set(structure.get_kind_names()), set(kinds_data.data.kind_names)))

    atom_props = {'spin_alpha': [], 'spin_beta': [], 'fixed': [], 'unfixed': [], 'ghosts': []}

    kind_dict = kinds_data.kind_dict

    for i, kind_name in enumerate(structure.get_site_kindnames()):
        if kind_dict[kind_name].get('spin_alpha', False):
            atom_props['spin_alpha'].append(i + 1)
        if kind_dict[kind_name].get('spin_beta', False):
            atom_props['spin_beta'].append(i + 1)
        if kind_dict[kind_name].get('ghost', False):
            atom_props['ghost'].append(i + 1)
        if kind_dict[kind_name].get('fixed', False):
            atom_props['fixed'].append(i + 1)
        if not kind_dict[kind_name].get('fixed', False):
            atom_props['unfixed'].append(i + 1)

    # we only need unfixed if there are fixed
    if not atom_props.pop('fixed'):
        atom_props.pop('unfixed')

    return atom_props
