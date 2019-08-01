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
from aiida_crystal17.gulp.parsers.raw.write_geometry import create_geometry_lines


def create_input_lines(
        potential,
        structures,
        observable_datas,
        observables,
        delta=None,
        dump_file='fitting.grs',
):
    """create the input file for a potential fitting

    Parameters
    ----------
    potential : aiida_crystal17.gulp.data.potential.EmpiricalPotential
        must include fitting flags
    structures : dict[str, aiida.StructureData]
        mapping of structure names to structures
    observable_datas : dict[str, aiida.orm.Dict]
        mapping of structure names to observable data for the structure
        (must have same keys as structures)
    observables: None or dict[str, callable]
        mapping of observable to a function that returns (value, weighting) from the observable_data.
    delta: None or float
        differencing interval for gradients (default 0.00001 or 0.0001 for relax)
    dump_file : str
        the name of the output dump file

    Returns
    -------
    list[str]
        the input lines
    list[str]
        a list of the structure names, in the order they appear in the input

    """
    lines = []
    snames = []

    # intial key words
    lines.append('fit noflags')
    lines.append('')

    if delta is not None:
        lines.append('delta')
        lines.append('{0:.8f}'.format(delta))
        lines.append('')

    # The following command makes a uniform shift
    # to the energies of all structures to remove
    # the constant offset => we are only fitting
    # the local curvature.
    lines.extend(['shift', str(1.0)])
    lines.append('')

    for name in sorted(structures.keys()):
        snames.append(name)
        lines.extend(create_geometry_lines(structures[name], name=name))
        lines.append('')
        lines.append('observables')

        for oname in sorted(observables.keys()):
            lines.append(oname)
            value, weighting = observables[oname](observable_datas[name])
            lines.append('{0:.8f} {1:.8f}'.format(value, weighting))

        lines.append('end')
        lines.append('')

    # Tell the program to fit the overall shift
    lines.extend(['vary', 'shift', 'end'])
    lines.append('')

    # Force Field
    lines.extend(potential.get_input_lines())

    lines.append('')
    lines.append('dump {}'.format(dump_file))
    # NOTE can also dump every interval ('noover' will output to separate files)

    return lines, snames
