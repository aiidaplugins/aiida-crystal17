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
from aiida_crystal17.gulp.potentials.base import PotentialWriterAbstract, PotentialContent
from aiida_crystal17.gulp.potentials.common import INDEX_SEP
from aiida_crystal17.validation import load_schema


class PotentialWriterLJ(PotentialWriterAbstract):
    """class for creating gulp lennard-jones type
    inter-atomic potential inputs
    """

    @classmethod
    def get_description(cls):
        return 'Lennard-Jones potential, of the form; E = A/r**m - B/r**n'

    @classmethod
    def _get_schema(cls):
        return load_schema('potential.lj.schema.json')

    @classmethod
    def _get_fitting_schema(cls):
        return load_schema('fitting.lj.schema.json')

    def _make_string(self, data, fitting_data=None):
        """write reaxff data in GULP input format

        Parameters
        ----------
        data : dict
            dictionary of data
        species_filter : list[str] or None
            list of atomic symbols to filter by

        Returns
        -------
        str:
            the potential file content
        int:
            number of potential flags for fitting

        """
        lines = []
        total_flags = 0
        num_fit = 0

        for indices in sorted(data['2body']):
            species = ['{:7s}'.format(data['species'][int(i)]) for i in indices.split(INDEX_SEP)]
            values = data['2body'][indices]
            lines.append('lennard {lj_m} {lj_n}'.format(lj_m=values.get('lj_m', 12), lj_n=values.get('lj_n', 6)))
            if 'lj_rmin' in values:
                values_string = '{lj_A:.8E} {lj_B:.8E} {lj_rmin:8.5f} {lj_rmax:8.5f}'.format(**values)
            else:
                values_string = '{lj_A:.8E} {lj_B:.8E} {lj_rmax:8.5f}'.format(**values)

            total_flags += 2

            if fitting_data is not None:
                flag_a = flag_b = 0
                if 'lj_A' in fitting_data.get('2body', {}).get(indices, []):
                    flag_a = 1
                if 'lj_B' in fitting_data.get('2body', {}).get(indices, []):
                    flag_b = 1
                num_fit += flag_a + flag_b
                values_string += ' {} {}'.format(flag_a, flag_b)

            lines.append(' '.join(species) + ' ' + values_string)

        return PotentialContent('\n'.join(lines), total_flags, num_fit)

    def read_exising(self, lines):
        """read an existing potential file

        Parameters
        ----------
        lines : list[str]

        Returns
        -------
        dict
            the potential data

        Raises
        ------
        IOError
            on parsing failure

        """
        lineno = 0
        symbol_set = set()
        terms = {}

        while lineno < len(lines):
            line = lines[lineno]
            if line.strip().startswith('lennard'):
                meta_values = line.strip().split()
                if len(meta_values) != 3:
                    raise IOError('expected `lennard` option to have only m & n variables: {}'.format(line))
                try:
                    lj_m = int(meta_values[1])
                    lj_n = int(meta_values[2])
                except ValueError:
                    raise IOError('expected `lennard` option to have only (integer) m & n variables: {}'.format(line))
                lineno, sset, results = self.read_atom_section(
                    lines, lineno + 1, number_atoms=2, global_args={
                        'lj_m': lj_m,
                        'lj_n': lj_n
                    })
                symbol_set.update(sset)
                terms.update(results)
            lineno += 1

        pot_data = {'species': sorted(symbol_set), '2body': {}}
        for key, value in terms.items():
            indices = '-'.join([str(pot_data['species'].index(term)) for term in key])
            variables = value['values'].split()
            if len(variables) in [3, 5]:
                pot_data['2body'][indices] = {
                    'lj_m': value['global']['lj_m'],
                    'lj_n': value['global']['lj_n'],
                    'lj_A': float(variables[0]),
                    'lj_B': float(variables[1]),
                    'lj_rmax': float(variables[2])
                }
            elif len(variables) in [4, 6]:
                pot_data['2body'][indices] = {
                    'lj_m': value['global']['lj_m'],
                    'lj_n': value['global']['lj_n'],
                    'lj_A': float(variables[0]),
                    'lj_B': float(variables[1]),
                    'lj_rmin': float(variables[2]),
                    'lj_rmax': float(variables[3])
                }
            else:
                raise IOError('expected 3, 4, 5 or 6 variables: {}'.format(value))

        return pot_data
