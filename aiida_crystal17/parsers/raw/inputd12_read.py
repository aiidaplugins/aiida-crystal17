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
module for reading main.d12 (for immigration)
"""
import numpy as np

from aiida_crystal17.common import get_keys, unflatten_dict
from aiida_crystal17.validation import load_schema, validate_against_schema


def _pop_line(lines, num=1):
    """extract the first line(s)"""
    for _ in range(num):
        pline = lines.pop(0)
    return pline.strip()


def _append_key(dct, key, value):
    """create a list or append to existing"""
    newval = dct.get(key, [])
    newval.append(value)
    dct[key] = newval


def _split_line(line):
    """split a line into a list of integers and/or floats"""
    out = []
    for val in line.split():
        try:
            val = int(val)
        except ValueError:
            val = float(val)
        out.append(val)
    if not out:
        raise ValueError('blank line')
    if len(out) == 1:
        out = out[0]
    return out


def _get_atom_prop(lines, ptype):
    """extract atoms"""
    line = _pop_line(lines)
    natoms = int(line)
    line = _pop_line(lines)
    vals = [int(i) for i in line.split()]
    if ptype in ['ghosts', 'fragment']:
        while len(vals) != natoms:
            line = _pop_line(lines)
            vals.extend([int(j) for j in line.split()])
        return vals, line
    elif ptype == 'atomspin':
        while len(vals) / 2 != natoms:
            line = _pop_line(lines)
            vals.extend([int(j) for j in line.split()])

        vals = np.reshape(vals, (natoms, 2))
        return (vals[vals[:, 1] == 1][:, 0].tolist(), vals[vals[:, 1] == -1][:, 0].tolist()), line
    else:
        raise ValueError('ptype: {}'.format(ptype))


def extract_data(input_string):
    """ extract data from a main.d12 CRYSTAL17 file

    - Any geometry creation commands are ignored
    - Basis sets must be included explicitly (no keywords) and are read into the basis_sets list
    - FRAGMENT, GHOSTS and ATOMSPIN commands are read into the atom_props dict
    - Otherwise, only commands contained in the inputd12.schema.json are allowed

    :param input_string: a string if the content of the file
    :returns param_dict: the parameter dict for use in ``crystal17.main`` calculation
    :returns basis_sets: a list of the basis sets
    :returns atom_props: a dictionary of atom specific values (spin_alpha, spin_beta, ghosts, fragment)

    """
    lines = input_string.splitlines()

    schema = load_schema('inputd12.schema.json')
    output_dict = {}
    basis_sets = []
    atom_props = {}

    output_dict['title'] = _pop_line(lines)

    _read_geom_block(lines, output_dict, schema)

    line = _pop_line(lines)

    if line == 'OPTGEOM':
        line = _read_geomopt_block(atom_props, line, lines, output_dict, schema)

    if line == 'BASISSET':
        raise NotImplementedError('key word basis set input (BASISSET)')
    if not line == 'END':
        raise IOError('expecting end of geom block: {}'.format(line))

    _read_basis_block(atom_props, basis_sets, lines, output_dict, schema)

    line = _pop_line(lines)

    _read_hamiltonian_block(atom_props, lines, output_dict, schema)

    output_dict = unflatten_dict(output_dict)
    validate_against_schema(output_dict, 'inputd12.schema.json')

    return output_dict, basis_sets, atom_props


def _read_hamiltonian_block(atom_props, lines, output_dict, schema):

    sblock = ['properties', 'scf', 'properties']

    while lines[0].strip() != 'END':
        line = _pop_line(lines)
        if line == 'DFT':
            _read_dft_block(lines, output_dict, schema)

            line = _pop_line(lines)
        elif line == 'SHRINK':
            line = _pop_line(lines)
            try:
                kis, kisp = line.split()
                kis = int(kis)
                kisp = int(kisp)
            except ValueError:
                raise IOError("expecting SHRINK in form 'is isp': {}".format(line))
            output_dict['scf.k_points'] = (kis, kisp)
        elif line in get_keys(schema, sblock + ['single', 'enum'], raise_error=True):
            output_dict['scf.single'] = line
        elif line in get_keys(schema, sblock + ['numerical', 'properties'], raise_error=True).keys():
            key = line
            if get_keys(schema, sblock + ['numerical', 'properties', key, 'type'], raise_error=True) == 'boolean':
                output_dict['scf.numerical.{}'.format(key)] = True
            else:
                line = _pop_line(lines)
                output_dict['scf.numerical.{}'.format(key)] = _split_line(line)
        elif line in get_keys(schema, sblock + ['post_scf', 'items', 'enum'], raise_error=True):
            _append_key(output_dict, 'scf.post_scf', line)
        elif line in get_keys(schema, sblock + ['spinlock', 'properties'], raise_error=True).keys():
            key = line
            line = _pop_line(lines)
            output_dict['scf.spinlock.{}'.format(key)] = _split_line(line)
        elif line in get_keys(schema, sblock + ['fock_mixing', 'oneOf', 0, 'enum'], raise_error=True):
            output_dict['scf.fock_mixing'] = line
        elif line == 'BROYDEN':
            line = _pop_line(lines)
            output_dict['scf.fock_mixing.BROYDEN'] = _split_line(line)
        elif line == 'ATOMSPIN':
            val, line = _get_atom_prop(lines, 'atomspin')
            atom_props['spin_alpha'] = val[0]
            atom_props['spin_beta'] = val[1]
        else:
            raise NotImplementedError('Hamiltonian Block: {}'.format(line))


def _read_dft_block(lines, output_dict, schema):
    correlat = None
    exchange = None
    while lines[0].strip() != 'END':
        line = _pop_line(lines)
        if line == 'SPIN':
            output_dict['scf.dft.SPIN'] = True
        elif line in get_keys(
                schema, ['properties', 'scf', 'properties', 'dft', 'properties', 'xc', 'oneOf', 1, 'enum'],
                raise_error=True):
            output_dict['scf.dft.xc'] = line
        elif line == 'CORRELAT':
            line = _pop_line(lines)
            correlat = line
        elif line == 'EXCHANGE':
            line = _pop_line(lines)
            exchange = line
        elif line == 'LSRSH-PBE':
            line = _pop_line(lines)
            output_dict['scf.dft.xc.LSRSH-PBE'] = _split_line(line)
        elif line in get_keys(
                schema, ['properties', 'scf', 'properties', 'dft', 'properties', 'grid', 'enum'], raise_error=True):
            output_dict['scf.dft.grid'] = line
        elif line in get_keys(
                schema, ['properties', 'scf', 'properties', 'dft', 'properties', 'grid_weights', 'enum'],
                raise_error=True):
            output_dict['scf.dft.grid_weights'] = line
        elif line in get_keys(
                schema, ['properties', 'scf', 'properties', 'dft', 'properties', 'numerical', 'properties'],
                raise_error=True).keys():
            key = line
            line = _pop_line(lines)
            output_dict['scf.dft.numerical.{}'.format(key)] = _split_line(line)
        else:
            raise NotImplementedError('DFT Block: {}'.format(line))
    if (correlat, exchange) != (None, None):
        if None in (correlat, exchange):
            raise IOError('found only one of CORRELAT EXCHANGE: {} {}'.format(correlat, exchange))
        output_dict['scf.dft.xc'] = (exchange, correlat)


def _read_basis_block(atom_props, basis_sets, lines, output_dict, schema):
    basis_lines = []
    while not lines[0].startswith('99 '):
        line = _pop_line(lines)
        basis_lines.append(line)
        try:
            anum, nshells = line.split()  # pylint: disable=unused-variable
            nshells = int(nshells)
        except ValueError:
            raise IOError("expected 'anum nshells': {}".format(line))
        for i in range(nshells):
            line = _pop_line(lines)
            basis_lines.append(line)
            try:
                btype, stype, nfuncs, _, _ = line.split()
                btype, stype, nfuncs = [int(i) for i in [btype, stype, nfuncs]]
                # charge, scale = [float(i) for i in [charge, scale]]
            except ValueError:
                raise IOError("expected 'btype, stype, nfuncs, charge, scale': {}".format(line))
            if btype == 0:
                for _ in range(nfuncs):
                    line = _pop_line(lines)
                    basis_lines.append(line)
        basis_sets.append('\n'.join(basis_lines))
        basis_lines = []
    line = _pop_line(lines)
    while lines[0].strip() != 'END':
        line = _pop_line(lines)
        if line in get_keys(schema, ['properties', 'basis_set', 'properties'], raise_error=True).keys():
            output_dict['basis_set.{}'.format(line)] = True
        elif line == 'GHOSTS':
            val, line = _get_atom_prop(lines, 'ghosts')
            atom_props['ghosts'] = val
        else:
            raise NotImplementedError('Basis Set Block: {}'.format(line))


def _read_geomopt_block(atom_props, line, lines, output_dict, schema):
    if lines[0].strip().startswith('END'):
        output_dict['geometry.optimise'] = True
    while not lines[0].strip().startswith('END'):
        line = _pop_line(lines)

        opt_keys = ['properties', 'geometry', 'properties', 'optimise', 'properties']

        if line in ['EXTPRESS']:
            raise NotImplementedError('GeomOpt Block: {}'.format(line))
        elif line in get_keys(schema, opt_keys + ['type', 'enum'], raise_error=True):
            output_dict['geometry.optimise.type'] = line
        elif line in get_keys(schema, opt_keys + ['hessian', 'enum'], raise_error=True):
            output_dict['geometry.optimise.hessian'] = line
        elif line in get_keys(schema, opt_keys + ['gradient', 'enum'], raise_error=True):
            output_dict['geometry.optimise.gradient'] = line
        elif line in get_keys(schema, opt_keys + ['info_print', 'items', 'enum'], raise_error=True):
            _append_key(output_dict, 'geometry.optimise.info_print', line)
        elif line in get_keys(schema, opt_keys + ['convergence', 'properties'], raise_error=True).keys():
            key = 'geometry.optimise.convergence.{}'.format(line)
            line = _pop_line(lines)
            try:
                output_dict[key] = int(line)
            except ValueError:
                output_dict[key] = float(line)
        elif line == 'FRAGMENT':
            val, line = _get_atom_prop(lines, 'fragment')
            atom_props['fragment'] = val
        else:
            raise NotImplementedError('OPTGEOM block: {}'.format(line))
    line = _pop_line(lines, 2)
    return line


def _read_geom_block(lines, output_dict, schema):
    while lines[0].strip() not in ['OPTGEOM', 'END']:

        line = _pop_line(lines)

        if line in [
                'FIELD', 'FIELDCON', 'CPHF', 'ELASTCON', 'EOS', 'FREQCALC', 'ANHARM', 'CONFCNT', 'CONFRAND', 'RUNCONFS',
                'MOLEBSSE', 'ATOMBSSE'
        ]:
            raise NotImplementedError('Geometry Block: {}'.format(line))
        elif line in get_keys(
                schema, ['properties', 'geometry', 'properties', 'info_print', 'items', 'enum'], raise_error=True):
            _append_key(output_dict, 'geometry.info_print', line)
        elif line in get_keys(
                schema, ['properties', 'geometry', 'properties', 'info_external', 'items', 'enum'], raise_error=True):
            _append_key(output_dict, 'geometry.info_external', line)
