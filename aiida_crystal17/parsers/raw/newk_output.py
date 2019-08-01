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
from aiida_crystal17 import __version__


def read_newk_content(fileobj, parser_class):

    results_data = {
        'parser_version': str(__version__),
        'parser_class': str(parser_class),
        'parser_errors': [],
        'parser_warnings': [],
        'errors': [],
        'warnings': []
    }

    fermi = None
    for line in fileobj:
        if 'FERMI ENERGY' in line:
            # if fermi is not None:
            #     results_data["parser_errors"].append(
            #         "found multiple instances of 'FERMI ENERGY'")
            # there is also FERMI ENERGY AND DENSITY MATRIX lower down
            elements = line.split()
            indx = None
            for i, element in enumerate(elements):
                if element == 'ENERGY':
                    indx = i + 1
                    break
            try:
                fermi = float(elements[indx])
            except Exception:
                results_data['parser_errors'].append('Could not extract fermi energy from line: {}'.format(line))

            break

    if fermi is None:
        results_data['parser_errors'].append("could not find 'FERMI ENERGY'")
    else:
        results_data['fermi_energy'] = fermi * 27.21138602
    results_data['energy_units'] = 'eV'

    # TODO read more data

    return results_data
