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
import copy

from collections import namedtuple
from aiida_crystal17.common.atoms import (GAUSSIAN_ORBITALS, ELECTRON_CONFIGURATIONS, SYMBOLS, SYMBOLS_R)


def parse_bsets_stdin(content, allow_comments=False, isolated=False):
    """parse basis sets from a crystal intput file

    Parameters
    ----------
    content : str
        file content to parse
    allow_comments : bool
        if True, comments will be stripped before parsing
    isolated : bool
        if the basis sets are not within the crystal input file

    Returns
    -------
    dict
        {'bs': {<atom_type>: [{'type': <type>, 'functions': [...]}, ...]},
         'ecp': {<atom_type>: [[...], ...]}}

    Raises
    ------
    IOError
        if an error occurs during the parsing
    NotImplementedError
        if more than 2 basis sets / pseudopotentials are set for one atom type

    Notes
    -----

    Standard Basis Set::

        a_number_id n_shells
        # for each shell
        type shell_type n_functions charge scale_factor
        # if type=0, for n_functions
        exponent contraction_coefficient

    The atomic number Z is given by the remainder of the division of the
    conventional atomic number by 100 (2 max per species in positions not symmetry-related):

    - a_number_id < 200 > 1000: all electron basis set
    - a_number_id > 200 < 1000: valence electron basis set

    Valence-electron only calculations can be performed with the aid of
    effective core pseudo-potentials (ECP).
    The ECP input must be inserted into the basis set input of the atoms with
    conventional atomic number>200.

    Effective core pseudo-potentials (ECP) section (p. 75)::

        INPUT / HAYWLC / HAYWSC / BARTHE / DURAND
        # if INPUT insert
        effective_core_charge M M0 M1 M2 M3 M4
        # insert M+M0+M1+M2+M3+M4 records
        a_kl C_kl n_kl

    """
    gbasis = {}

    if not content:
        raise IOError('content is empty')

    comment_signals = '#/*<!'
    bs_sequence = {0: 'S', 1: 'SP', 2: 'P', 3: 'D', 4: 'F', 5: 'G'}
    bs_type = {
        1: 'STO-nG(nd) type ',  # Pople standard STO-nG (Z=1-54);
        2: '3(6)-21G(nd) type '  # Pople standard 3(6)-21G (Z=1-54(18)) + standard polarization functions
    }
    bs_notation = {
        1: 'n-21G outer valence shell',
        2: 'n-21G inner valence shell',
        3: '3-21G core shell',
        6: '6-21G core shell'
    }
    ps_keywords = {
        'INPUT': None,
        'HAYWLC': 'Hay-Wadt large core',
        'HAYWSC': 'Hay-Wadt small core',
        'BARTHE': 'Durand-Barthelat',
        'DURAND': 'Durand-Barthelat'
    }
    ps_sequence = ['W0', 'P0', 'P1', 'P2', 'P3', 'P4']

    in_basis_section = isolated
    in_pseudo, in_basis = False, False
    atomic_symbol = atomic_number_id = distrib = ps_indices_map = None

    for lineno, line in enumerate(content.splitlines(), 1):

        # ignore input until reaching the end of the geometry/optimisation section
        if line.startswith('END'):
            in_basis_section = True
            continue

        if not in_basis_section:
            continue

        # strip end of line comments
        if allow_comments:
            for s in comment_signals:
                pos = line.find(s)
                if pos != -1:
                    line = line[:pos]
                    break

        parts = line.split()

        if len(parts) == 0:
            continue

        if len(parts) == 1 and parts[0].upper() in ps_keywords:
            # start of pseudo
            if atomic_symbol is None:
                raise IOError('line {}; reached pseudo before setting atom type'.format(lineno))

            if not 200 < atomic_number_id < 999:
                raise IOError(
                    'line {}; the basis contains an ecp, but the atomic_id {} is not in the range [200, 999]'.format(
                        lineno, atomic_number_id))

            if parts[0] != 'INPUT':
                gbasis[atomic_symbol]['ecp'].append(ps_keywords[parts[0].upper()])

            continue

        # sanity check
        try:
            [float(p.replace('D', 'E')) for p in parts]
        except ValueError:
            in_basis_section = False
            continue

        if len(parts) in [2, 3]:

            if parts[0] == '99' and parts[1] == '0':
                # end of basis set section
                break

            elif '.' in parts[0] or '.' in parts[1]:
                # exponent section for bs or ecp
                parts = [float(x.replace('D', 'E')) for x in parts]

                if in_pseudo:
                    # distribute exponents into ecp-types according to counter, that we now calculate
                    if distrib in list(ps_indices_map.keys()):
                        gbasis[atomic_symbol]['ecp'].append([ps_indices_map[distrib]])
                    gbasis[atomic_symbol]['ecp'][-1].append(tuple(parts))
                    distrib += 1
                elif in_basis:
                    # distribute exponents into orbitals according to counter, that we already defined
                    gbasis[atomic_symbol]['bs'][-1]['functions'].append(tuple(parts))

            else:
                # atom type definition section
                atomic_number_id = int(parts[0])
                atomic_number = atomic_number_id % 100

                if atomic_number == 0:
                    atomic_symbol = 'X'
                else:
                    if atomic_number not in SYMBOLS:
                        raise IOError('line {}; atomic number not recognised: {}'.format(lineno, atomic_number))
                    atomic_symbol = SYMBOLS[atomic_number]

                if atomic_symbol in gbasis:
                    if atomic_symbol + '1' in gbasis:
                        raise NotImplementedError('line {}; More than two different basis sets for element {}'.format(
                            lineno, atomic_symbol))
                    atomic_symbol += '1'

                if 200 < atomic_number_id < 999:
                    gbasis[atomic_symbol] = {'type': 'valence-electron', 'bs': [], 'ecp': []}
                else:
                    gbasis[atomic_symbol] = {'type': 'all-electron', 'bs': []}

        elif len(parts) == 5:
            # orbital section
            gbasis[atomic_symbol]['bs'].append({'type': bs_sequence[int(parts[1])], 'functions': []})
            parts = list(map(int, parts[0:3]))

            if parts[0] == 0:
                # insert from data given in input
                in_pseudo, in_basis = False, True

            elif parts[0] in bs_type:
                # pre-defined insert
                if parts[2] in bs_notation:
                    gbasis[atomic_symbol]['bs'][-1]['functions'].append(bs_type[parts[0]] + bs_notation[parts[2]])
                else:
                    gbasis[atomic_symbol]['bs'][-1]['functions'].append(bs_type[parts[0]] + 'n=' + str(parts[2]))

        elif 6 <= len(parts) <= 7:
            # pseudo - INPUT section
            parts.pop(0)
            ps_indices = list(map(int, parts))
            ps_indices_map = {}
            accum = 1
            for c, n in enumerate(ps_indices):
                if n == 0:
                    continue
                ps_indices_map[accum] = ps_sequence[c]
                accum += n
            distrib = 1
            in_pseudo, in_basis = True, False

    for k, v in gbasis.items():
        # sometimes no BS for host atom is printed when it is replaced by Xx: account for it
        if not len(v['bs']) and k != 'X' and 'X' in gbasis:
            gbasis[k] = copy.deepcopy(gbasis['X'])
        # NOTE: no GHOST deletion should be performed, since it breaks orbitals order for band structure plotting

    return gbasis


OrbitalResult = namedtuple('OrbitalResult', ['electrons', 'core_electrons', 'number_ao', 'orbital_types', 'ao_indices'])


def compute_orbitals(atoms, basis_sets):
    # type: (list, dict) -> OrbitalResult
    """compute data for all atomic orbitals in a structure,
    given elemental representations by crystal basis sets

    Parameters
    ----------
    atoms : list[str] or list[int]
        list of atomic numbers or symbols which the structure comprises of
    basis_sets : dict[str, dict]
        basis set data, in the format returned from ``parse_bsets_stdin``

    Returns
    -------
    OrbitalResult

    """
    total_electrons = total_core_electrons = total_aos = 0
    aos_indices = {}
    orbital_types = []

    for atom_index, atom in enumerate(atoms):
        try:
            electrons = int(atom)
            symbol = SYMBOLS[int(atom)]
        except (TypeError, ValueError):
            symbol = atom
            electrons = SYMBOLS_R[atom]
        if basis_sets[symbol]['type'] == 'valence-electron':
            raise NotImplementedError('computing for bases with core pseudopotentials')
        outer_electrons = sum([i for n, i in ELECTRON_CONFIGURATIONS[electrons]['outer']])
        total_electrons += electrons
        total_core_electrons += electrons - outer_electrons
        type_count = {}
        for orbital in basis_sets[symbol]['bs']:
            type_count.setdefault(orbital['type'], 0)
            type_count[orbital['type']] += 1
            for i in range(GAUSSIAN_ORBITALS[orbital['type']]):
                total_aos += 1
                if (symbol, orbital['type'], type_count[orbital['type']]) not in orbital_types:
                    orbital_types.append((symbol, orbital['type'], type_count[orbital['type']]))
                aos_indices[total_aos] = {
                    'atom': atom_index,
                    'element': symbol,
                    'type': orbital['type'],
                    'index': type_count[orbital['type']]
                }

    return OrbitalResult(total_electrons, total_core_electrons, total_aos, orbital_types, aos_indices)
