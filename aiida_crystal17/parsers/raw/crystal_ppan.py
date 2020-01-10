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
from aiida_crystal17.common.parsing import split_numbers


def parse_crystal_ppan(content):
    """Parse CRYSTAL Mulliken Population outputs (PPAN.DAT)

    Parameters
    ----------
    content: str

    Notes
    -----

    Format:

    ::

        NSPIN,NATOM
        IAT,NSHELL
        Xiat,Yiat,Ziat (AU)
        QTOT shell charges
        NORB
        orbital charges
    """
    spin_names = ['alpha+beta_electrons', 'alpha-beta_electrons']
    data = {}
    lines = content.splitlines()
    line = _new_line(lines)
    nspin, natoms = split_numbers(line)
    for spin_num in range(int(nspin)):
        spin_name = spin_names[spin_num]
        spin_data = data.setdefault(spin_name, {'atoms': []})
        for atom_num in range(int(natoms)):
            line = _new_line(lines)
            atomic_number, nshell = split_numbers(line)
            line = _new_line(lines)
            coordinate = split_numbers(line)
            line = _new_line(lines)
            values = split_numbers(line)
            total_charge = values[0]
            shell_charges = values[1:]
            while len(shell_charges) < nshell:
                line = _new_line(lines)
                shell_charges.extend(split_numbers(line))
            line = _new_line(lines)
            (norbitals,) = split_numbers(line)
            orbital_charges = []
            while len(orbital_charges) < norbitals:
                line = _new_line(lines)
                orbital_charges.extend(split_numbers(line))
            spin_data['atoms'].append({
                'atomic_number': atomic_number,
                'coordinate': coordinate,
                'total_charge': total_charge,
                'shell_charges': shell_charges,
                'orbital_charges': orbital_charges
            })
        spin_data['summed_charge'] = sum(a['total_charge'] for a in spin_data['atoms'])
    return data


def _new_line(lines):
    try:
        line = lines.pop(0).strip()
        while not line or line.startswith('#'):
            line = lines.pop(0).strip()
        return line
    except IndexError:
        raise IOError('Reached bottom of file, before parsing all data')
