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
from collections import OrderedDict
import textwrap

from aiida_crystal17.common.parsing import split_numbers
from aiida_crystal17.validation import validate_against_schema
from aiida_crystal17.gulp.potentials.common import INDEX_SEP

KEYS_GLOBAL = ('reaxff0_boc1', 'reaxff0_boc2', 'reaxff3_coa2', 'Triple bond stabilisation 1',
               'Triple bond stabilisation 2', 'C2-correction', 'reaxff0_ovun6', 'Triple bond stabilisation',
               'reaxff0_ovun7', 'reaxff0_ovun8', 'Triple bond stabilization energy', 'Lower Taper-radius',
               'Upper Taper-radius', 'reaxff2_pen2', 'reaxff0_val7', 'reaxff0_lp1', 'reaxff0_val9', 'reaxff0_val10',
               'Not used 2', 'reaxff0_pen2', 'reaxff0_pen3', 'reaxff0_pen4', 'Not used 3', 'reaxff0_tor2',
               'reaxff0_tor3', 'reaxff0_tor4', 'Not used 4', 'reaxff0_cot2', 'reaxff0_vdw1', 'bond order cutoff',
               'reaxff3_coa4', 'reaxff0_ovun4', 'reaxff0_ovun3', 'reaxff0_val8', 'Not used 5', 'Not used 6',
               'Not used 7', 'Not used 8', 'reaxff3_coa3')

# TODO some variables lammps sets as global are actually species dependant in GULP, how to handle these?

KEYS_1BODY = ('reaxff1_radii1', 'reaxff1_valence1', 'mass', 'reaxff1_morse3', 'reaxff1_morse2', 'reaxff_gamma',
              'reaxff1_radii2', 'reaxff1_valence3', 'reaxff1_morse1', 'reaxff1_morse4', 'reaxff1_valence4',
              'reaxff1_under', 'dummy1', 'reaxff_chi', 'reaxff_mu', 'dummy2', 'reaxff1_radii3', 'reaxff1_lonepair2',
              'dummy3', 'reaxff1_over2', 'reaxff1_over1', 'reaxff1_over3', 'dummy4', 'dummy5', 'reaxff1_over4',
              'reaxff1_angle1', 'dummy11', 'reaxff1_valence2', 'reaxff1_angle2', 'dummy6', 'dummy7', 'dummy8')

KEYS_2BODY_BONDS = ('reaxff2_bond1', 'reaxff2_bond2', 'reaxff2_bond3', 'reaxff2_bond4', 'reaxff2_bo5', 'reaxff2_bo7',
                    'reaxff2_bo6', 'reaxff2_over', 'reaxff2_bond5', 'reaxff2_bo3', 'reaxff2_bo4', 'dummy1',
                    'reaxff2_bo1', 'reaxff2_bo2', 'reaxff2_bo8', 'reaxff2_pen1')

KEYS_2BODY_OFFDIAG = [
    'reaxff2_morse1', 'reaxff2_morse3', 'reaxff2_morse2', 'reaxff2_morse4', 'reaxff2_morse5', 'reaxff2_morse6'
]

KEYS_3BODY_ANGLES = ('reaxff3_angle1', 'reaxff3_angle2', 'reaxff3_angle3', 'reaxff3_coa1', 'reaxff3_angle5',
                     'reaxff3_penalty', 'reaxff3_angle4')

KEYS_3BODY_HBOND = ('reaxff3_hbond1', 'reaxff3_hbond2', 'reaxff3_hbond3', 'reaxff3_hbond4')

KEYS_4BODY_TORSION = ('reaxff4_torsion1', 'reaxff4_torsion2', 'reaxff4_torsion3', 'reaxff4_torsion4',
                      'reaxff4_torsion5', 'dummy1', 'dummy2')

DEFAULT_TOLERANCES = {
    'anglemin': 0.001,
    'angleprod': 0.001,  # Hard coded to 0.001 in original code.
    'hbondmin': 0.01,  # Hard coded to 0.01 in original code.
    'hbonddist': 7.5,  # Hard coded to 7.5 Ang in original code.
    'torsionprod': 0.00001
}

# NOTE: torsionprod needs to be lower (0.001), to get comparable energy to lammps,
# but then won't optimize (reaches maximum steps)


def read_lammps_format(lines):
    """ read a reaxff file, in lammps format, to a standardised potential dictionary """
    output = {
        'description': lines[0],
        'global': {},
        'species': ['X core'],  # X is always first
        '1body': {},
        '2body': {},
        '3body': {},
        '4body': {}
    }

    lineno = 1

    # Global parameters
    if lines[lineno].split()[0] != str(len(KEYS_GLOBAL)):
        raise IOError('Expecting {} global parameters'.format(len(KEYS_GLOBAL)))

    for key in KEYS_GLOBAL:
        lineno += 1
        output['global'][key] = float(lines[lineno].split()[0])

    output['global']['reaxff2_pen3'] = 1.0  # this is not provided by lammps, but is used by GULP

    # one-body parameters
    lineno += 1
    num_species = int(lines[lineno].split()[0])
    lineno += 3
    idx = 1
    for i in range(num_species):
        lineno += 1
        symbol, values = lines[lineno].split(None, 1)
        if symbol == 'X':
            species_idx = 0  # the X symbol is always assigned index 0
        else:
            species_idx = idx
            idx += 1
            output['species'].append(symbol + ' core')
        values = split_numbers(values)
        for _ in range(3):
            lineno += 1
            values.extend(split_numbers(lines[lineno]))

        if len(values) != len(KEYS_1BODY):
            raise Exception('number of values different than expected for species {0}, '
                            '{1} != {2}'.format(symbol, len(values), len(KEYS_1BODY)))

        key_map = {k: v for k, v in zip(KEYS_1BODY, values)}
        key_map['reaxff1_lonepair1'] = 0.5 * (key_map['reaxff1_valence3'] - key_map['reaxff1_valence1'])

        output['1body'][str(species_idx)] = key_map

    # two-body bond parameters
    lineno += 1
    num_lines = int(lines[lineno].split()[0])
    lineno += 2
    for _ in range(num_lines):
        values = split_numbers(lines[lineno]) + split_numbers(lines[lineno + 1])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        key_name = '{}-{}'.format(species_idx1, species_idx2)
        lineno += 2

        if len(values) != len(KEYS_2BODY_BONDS):
            raise Exception('number of bond values different than expected for key {0}, '
                            '{1} != {2}'.format(key_name, len(values), len(KEYS_2BODY_BONDS)))

        output['2body'][key_name] = {k: v for k, v in zip(KEYS_2BODY_BONDS, values)}

    # two-body off-diagonal parameters
    num_lines = int(lines[lineno].split()[0])
    lineno += 1
    for _ in range(num_lines):
        values = split_numbers(lines[lineno])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        key_name = '{}-{}'.format(species_idx1, species_idx2)
        lineno += 1

        if len(values) != len(KEYS_2BODY_OFFDIAG):
            raise Exception('number of off-diagonal values different than expected for key {0} (line {1}), '
                            '{2} != {3}'.format(key_name, lineno - 1, len(values), len(KEYS_2BODY_OFFDIAG)))

        output['2body'].setdefault(key_name, {}).update({k: v for k, v in zip(KEYS_2BODY_OFFDIAG, values)})

    # three-body angle parameters
    num_lines = int(lines[lineno].split()[0])
    lineno += 1
    for _ in range(num_lines):
        values = split_numbers(lines[lineno])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        species_idx3 = int(values.pop(0))
        key_name = '{}-{}-{}'.format(species_idx1, species_idx2, species_idx3)
        lineno += 1

        if len(values) != len(KEYS_3BODY_ANGLES):
            raise Exception('number of angle values different than expected for key {0} (line {1}), '
                            '{2} != {3}'.format(key_name, lineno - 1, len(values), len(KEYS_3BODY_ANGLES)))

        output['3body'].setdefault(key_name, {}).update({k: v for k, v in zip(KEYS_3BODY_ANGLES, values)})

    # four-body torsion parameters
    num_lines = int(lines[lineno].split()[0])
    lineno += 1
    for _ in range(num_lines):
        values = split_numbers(lines[lineno])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        species_idx3 = int(values.pop(0))
        species_idx4 = int(values.pop(0))
        key_name = '{}-{}-{}-{}'.format(species_idx1, species_idx2, species_idx3, species_idx4)
        lineno += 1

        if len(values) != len(KEYS_4BODY_TORSION):
            raise Exception('number of torsion values different than expected for key {0} (line {1}), '
                            '{2} != {3}'.format(key_name, lineno - 1, len(values), len(KEYS_4BODY_TORSION)))

        output['4body'].setdefault(key_name, {}).update({k: v for k, v in zip(KEYS_4BODY_TORSION, values)})

    # three-body h-bond parameters
    num_lines = int(lines[lineno].split()[0])
    lineno += 1
    for _ in range(num_lines):
        values = split_numbers(lines[lineno])
        species_idx1 = int(values.pop(0))
        species_idx2 = int(values.pop(0))
        species_idx3 = int(values.pop(0))
        key_name = '{}-{}-{}'.format(species_idx1, species_idx2, species_idx3)
        lineno += 1

        if len(values) != len(KEYS_3BODY_HBOND):
            raise Exception('number of h-bond values different than expected for key {0} (line {1}), '
                            '{2} != {3}'.format(key_name, lineno - 1, len(values), len(KEYS_3BODY_HBOND)))

        output['3body'].setdefault(key_name, {}).update({k: v for k, v in zip(KEYS_3BODY_HBOND, values)})

    return output


def format_lammps_value(value):
    return '{:.4f}'.format(value)


def write_lammps_format(data):
    """ write a reaxff file, in lammps format, from a standardised potential dictionary """
    # validate dictionary
    validate_against_schema(data, 'potential.reaxff.schema.json')

    output = [data['description']]

    # Global parameters
    output.append('{} ! Number of general parameters'.format(len(KEYS_GLOBAL)))
    for key in KEYS_GLOBAL:
        output.append('{0:.4f} ! {1}'.format(data['global'][key], key))

    # one-body parameters
    output.extend([
        '{0} ! Nr of atoms; cov.r; valency;a.m;Rvdw;Evdw;gammaEEM;cov.r2;#'.format(len(data['species'])),
        'alfa;gammavdW;valency;Eunder;Eover;chiEEM;etaEEM;n.u.', 'cov r3;Elp;Heat inc.;n.u.;n.u.;n.u.;n.u.',
        'ov/un;val1;n.u.;val3,vval4'
    ])
    for i, species in enumerate(data['species']):
        if species.endswith('shell'):
            raise ValueError('only core species can be used for reaxff, not shell: {}'.format(species))
        species = species[:-5]
        output.extend([
            species + ' ' + ' '.join([format_lammps_value(data['1body'][str(i)][k]) for k in KEYS_1BODY[:8]]),
            ' '.join([format_lammps_value(data['1body'][str(i)][k]) for k in KEYS_1BODY[8:16]]), ' '.join([
                format_lammps_value(data['1body'][str(i)][k]) for k in KEYS_1BODY[16:24]
            ]), ' '.join([format_lammps_value(data['1body'][str(i)][k]) for k in KEYS_1BODY[24:32]])
        ])

    # two-body angle parameters
    suboutout = []
    for key in sorted(data['2body']):
        subdata = data['2body'][key]
        if not set(subdata.keys()).issuperset(KEYS_2BODY_BONDS):
            continue
        suboutout.extend([
            ' '.join(key.split(INDEX_SEP)) + ' ' + ' '.join(
                [format_lammps_value(subdata[k]) for k in KEYS_2BODY_BONDS[:8]]),
            ' '.join([format_lammps_value(subdata[k]) for k in KEYS_2BODY_BONDS[8:16]])
        ])

    output.extend([
        '{0} ! Nr of bonds; Edis1;LPpen;n.u.;pbe1;pbo5;13corr;pbo6'.format(int(len(suboutout) / 2)),
        'pbe2;pbo3;pbo4;n.u.;pbo1;pbo2;ovcorr'
    ] + suboutout)

    # two-body off-diagonal parameters
    suboutout = []
    for key in sorted(data['2body']):
        subdata = data['2body'][key]
        if not set(subdata.keys()).issuperset(KEYS_2BODY_OFFDIAG):
            continue
        suboutout.extend([
            ' '.join(key.split(INDEX_SEP)) + ' ' + ' '.join(
                [format_lammps_value(subdata[k]) for k in KEYS_2BODY_OFFDIAG]),
        ])

    output.extend(['{0} ! Nr of off-diagonal terms; Ediss;Ro;gamma;rsigma;rpi;rpi2'.format(len(suboutout))] + suboutout)

    # three-body angle parameters
    suboutout = []
    for key in sorted(data['3body']):
        subdata = data['3body'][key]
        if not set(subdata.keys()).issuperset(KEYS_3BODY_ANGLES):
            continue
        suboutout.extend([
            ' '.join(key.split(INDEX_SEP)) + ' ' + ' '.join(
                [format_lammps_value(subdata[k]) for k in KEYS_3BODY_ANGLES]),
        ])

    output.extend(['{0} ! Nr of angles;at1;at2;at3;Thetao,o;ka;kb;pv1;pv2'.format(len(suboutout))] + suboutout)

    # four-body torsion parameters
    suboutout = []
    for key in sorted(data['4body']):
        subdata = data['4body'][key]
        if not set(subdata.keys()).issuperset(KEYS_4BODY_TORSION):
            continue
        suboutout.extend([
            ' '.join(key.split(INDEX_SEP)) + ' ' + ' '.join(
                [format_lammps_value(subdata[k]) for k in KEYS_4BODY_TORSION]),
        ])

    output.extend(['{0} ! Nr of torsions;at1;at2;at3;at4;;V1;V2;V3;V2(BO);vconj;n.u;n'.format(len(suboutout))] +
                  suboutout)

    # three-body h-bond parameters
    suboutout = []
    for key in sorted(data['3body']):
        subdata = data['3body'][key]
        if not set(subdata.keys()).issuperset(KEYS_3BODY_HBOND):
            continue
        suboutout.extend([
            ' '.join(key.split(INDEX_SEP)) + ' ' + ' '.join([format_lammps_value(subdata[k]) for k in KEYS_3BODY_HBOND])
        ])

    output.extend(['{0} ! Nr of hydrogen bonds;at1;at2;at3;Rhb;Dehb;vhb1'.format(len(suboutout))] + suboutout)

    output.append('')

    return '\n'.join(output)


def write_gulp_format(data, fitting_data=None, global_val_fmt='{:.5E}', species_val_fmt='{:.5E}'):
    """ write a reaxff file, in GULP format, from a standardised potential dictionary

    NOTE: GULP only read a line up to ~80 characters,
    `&` can be used to break a line into two lines
    NOTE GULP outputs to 6 dp

    energies should be supplied in kcal (the default of the lammps file format)
    """
    # validate dictionary
    validate_against_schema(data, 'potential.reaxff.schema.json')

    if fitting_data is not None:
        validate_against_schema(fitting_data, 'fitting.reaxff.schema.json')

    for species in data['species']:
        if species.endswith('shell'):
            # TODO is this true?
            raise ValueError('only core species can be used for reaxff, not shell: {}'.format(species))
        species = species[:-5]

    total_flags = 0  # total number of variables with a flag
    fitting_flags = 0  # number of variables with a flag set to 1

    # header
    output = [
        '#',
        '#  ReaxFF force field',
        '#',
        '#  Original paper:',
        '#',
        '#  A.C.T. van Duin, S. Dasgupta, F. Lorant and W.A. Goddard III,',
        '#  J. Phys. Chem. A, 105, 9396-9409 (2001)',
        '#',
        '#  Parameters description:',
        '#',
        '# {}'.format(data['description']),
        '#',
        '#  Cutoffs for VDW & Coulomb terms',
        '#',
        'reaxFFvdwcutoff {:14.6E}'.format(data['global']['Upper Taper-radius']),
        'reaxFFqcutoff   {:14.6E}'.format(data['global']['Upper Taper-radius']),
        '#',
        '#  Bond order threshold - check anglemin as this is cutof2 given in control file',
        '#',
        'reaxFFtol  {:.6E} {:.6E} {:.6E} &'.format(
            data['global']['bond order cutoff'] * 0.01,
            *[data['global'].get(k, DEFAULT_TOLERANCES[k]) for k in 'anglemin angleprod'.split()]),
        '           {:.6E} {:.6E} {:.6E}'.format(
            *[data['global'].get(k, DEFAULT_TOLERANCES[k]) for k in 'hbondmin hbonddist torsionprod'.split()]),
        '#',
    ]

    # global parameters
    output.append('#  Species independent parameters')
    output.append('#')

    fields = OrderedDict([('reaxff0_bond', ['reaxff0_boc1', 'reaxff0_boc2']),
                          ('reaxff0_over',
                           ['reaxff0_ovun3', 'reaxff0_ovun4', 'reaxff0_ovun6', 'reaxff0_ovun7', 'reaxff0_ovun8']),
                          ('reaxff0_valence', ['reaxff0_val7', 'reaxff0_val8', 'reaxff0_val9', 'reaxff0_val10']),
                          ('reaxff0_penalty', ['reaxff0_pen2', 'reaxff0_pen3', 'reaxff0_pen4']),
                          ('reaxff0_torsion', ['reaxff0_tor2', 'reaxff0_tor3', 'reaxff0_tor4', 'reaxff0_cot2']),
                          ('reaxff0_vdw', ['reaxff0_vdw1']), ('reaxff0_lonepair', ['reaxff0_lp1'])])

    for field, variables in fields.items():
        total_flags += len(variables)
        string = '{:17}'.format(field) + ' '.join([global_val_fmt.format(data['global'][v]) for v in variables])
        if fitting_data is not None:
            fitting_flags += sum([1 if v in fitting_data.get('global', []) else 0 for v in variables])
            string += ' ' + ' '.join(['1' if v in fitting_data.get('global', []) else '0' for v in variables])

        lines = textwrap.wrap(string, 78)

        if len(lines) > 2:
            raise IOError('the line cannot be coerced to fit within the 80 character limit: {}'.format(string))
        elif len(lines) > 1:
            output.append('{} &'.format(lines[0]))
            output.append('    {}'.format(lines[1]))
        else:
            output.append(string)

    # one-body parameters
    output.append('#')
    output.append('#  One-Body Parameters')
    output.append('#')

    fields = {
        'reaxff1_radii': ['reaxff1_radii1', 'reaxff1_radii2', 'reaxff1_radii3'],
        'reaxff1_valence': ['reaxff1_valence1', 'reaxff1_valence2', 'reaxff1_valence3', 'reaxff1_valence4'],
        'reaxff1_over': ['reaxff1_over1', 'reaxff1_over2', 'reaxff1_over3', 'reaxff1_over4'],
        'reaxff1_under': ['reaxff1_under'],
        'reaxff1_lonepair': ['reaxff1_lonepair1', 'reaxff1_lonepair2'],
        'reaxff1_angle': ['reaxff1_angle1', 'reaxff1_angle2'],
        'reaxff1_morse': ['reaxff1_morse1', 'reaxff1_morse2', 'reaxff1_morse3', 'reaxff1_morse4'],
        'reaxff_chi': ['reaxff_chi'],
        'reaxff_mu': ['reaxff_mu'],
        'reaxff_gamma': ['reaxff_gamma']
    }

    arguments = {'reaxff1_under': ['kcal'], 'reaxff1_lonepair': ['kcal'], 'reaxff1_morse': ['kcal']}

    field_lines, num_vars, num_fit = create_gulp_fields(
        data, '1body', fields, species_val_fmt, arguments=arguments, fitting_data=fitting_data)
    total_flags += num_vars
    fitting_flags += num_fit
    output.extend(field_lines)

    # two-body bond parameters
    output.append('#')
    output.append('#  Two-Body Parameters')
    output.append('#')

    fields = {
        'reaxff2_bo': ['reaxff2_bo1', 'reaxff2_bo2', 'reaxff2_bo3', 'reaxff2_bo4', 'reaxff2_bo5', 'reaxff2_bo6'],
        'reaxff2_bond': ['reaxff2_bond1', 'reaxff2_bond2', 'reaxff2_bond3', 'reaxff2_bond4', 'reaxff2_bond5'],
        'reaxff2_over': ['reaxff2_over'],
        'reaxff2_pen': ['reaxff2_pen1', 'global.reaxff2_pen2', 'global.reaxff2_pen'],
        'reaxff2_morse':
        ['reaxff2_morse1', 'reaxff2_morse2', 'reaxff2_morse3', 'reaxff2_morse4', 'reaxff2_morse5', 'reaxff2_morse6']
    }

    def reaxff2_bo_args(bodata):
        if bodata['reaxff2_bo7'] <= 0.001 and bodata['reaxff2_bo8'] <= 0.001:
            return ''
        elif bodata['reaxff2_bo7'] > 0.001 and bodata['reaxff2_bo8'] > 0.001:
            return 'over bo13'  # correct for overcoordination using f1 and 1-3 terms using f4 and f5
        elif bodata['reaxff2_bo7'] > 0.001 and bodata['reaxff2_bo8'] <= 0.001:
            return 'bo13'  # correct for 1-3 terms using f4 and f5
        elif bodata['reaxff2_bo7'] <= 0.001 and bodata['reaxff2_bo8'] > 0.001:
            return 'over'  # correct for overcoordination using f1
        return ''

    arguments = {
        'reaxff2_bo': reaxff2_bo_args,
        'reaxff2_bond': ['kcal'],
        'reaxff2_pen': ['kcal'],
        'reaxff2_morse': ['kcal']
    }

    conditions = {'reaxff2_pen': lambda s: s['reaxff2_pen1'] > 0.0}

    field_lines, num_vars, num_fit = create_gulp_fields(
        data, '2body', fields, species_val_fmt, conditions, arguments=arguments, fitting_data=fitting_data)
    total_flags += num_vars
    fitting_flags += num_fit
    output.extend(field_lines)

    # three-body parameters
    output.append('#')
    output.append('#  Three-Body Parameters')
    output.append('#')

    fields = {
        'reaxff3_angle':
        ['reaxff3_angle1', 'reaxff3_angle2', 'reaxff3_angle3', 'reaxff3_angle4', 'reaxff3_angle5', 'reaxff3_angle6'],
        # TODO reaxff3_angle6 is taken from a global value, if not present,
        # need to find out what this value is, so it can be set in the input data
        'reaxff3_penalty': ['reaxff3_penalty'],
        'reaxff3_conjugation': ['reaxff3_coa1', 'global.reaxff3_coa2', 'global.reaxff3_coa3', 'global.reaxff3_coa4'],
        'reaxff3_hbond': ['reaxff3_hbond1', 'reaxff3_hbond2', 'reaxff3_hbond3', 'reaxff3_hbond4']
    }

    arguments = {
        'reaxff3_angle': ['kcal'],
        'reaxff3_penalty': ['kcal'],
        'reaxff2_pen': ['kcal'],
        'reaxff3_conjugation': ['kcal'],
        'reaxff3_hbond': ['kcal']
    }

    conditions = {
        'reaxff3_angle': lambda s: s['reaxff3_angle2'] > 0.0,
        'reaxff3_conjugation': lambda s: abs(s['reaxff3_coa1']) > 1.0E-4
    }

    field_lines, num_vars, num_fit = create_gulp_fields(
        data, '3body', fields, species_val_fmt, conditions, arguments=arguments, fitting_data=fitting_data)
    total_flags += num_vars
    fitting_flags += num_fit
    output.extend(field_lines)

    # four-body parameters
    # TODO there seems to be an issue when flagging more than one torsion variable for fitting
    # the dump file just shows the first flagged variable as 1, then subsequent as 0
    output.append('#')
    output.append('#  Four-Body Parameters')
    output.append('#')

    fields = {
        'reaxff4_torsion':
        ['reaxff4_torsion1', 'reaxff4_torsion2', 'reaxff4_torsion3', 'reaxff4_torsion4', 'reaxff4_torsion5'],
    }

    arguments = {'reaxff4_torsion': ['kcal']}

    field_lines, num_vars, num_fit = create_gulp_fields(
        data, '4body', fields, species_val_fmt, arguments=arguments, fitting_data=fitting_data)
    total_flags += num_vars
    fitting_flags += num_fit
    output.extend(field_lines)

    output.append('')

    return '\n'.join(output), total_flags, fitting_flags


def create_gulp_fields(data, data_type, fields, species_val_fmt, conditions=None, arguments=None, fitting_data=None):
    """ create a subsection of the gulp output file"""
    if conditions is None:
        conditions = {}
    if arguments is None:
        arguments = {}
    num_of_variable = 0
    num_fit = 0

    output = []

    for field in sorted(fields):
        keys = fields[field]
        subdata = {}
        for indices in sorted(data[data_type]):
            num_of_variable += len(keys)
            local_keys = [k for k in keys if not k.startswith('global.') and k != 'reaxff3_angle6']
            if not set(data[data_type][indices].keys()).issuperset(local_keys):
                continue
            if field in conditions:
                try:
                    satisfied = conditions[field](data[data_type][indices])
                except KeyError:
                    continue
                if not satisfied:
                    continue
            species = ['{:7s}'.format(data['species'][int(i)]) for i in indices.split(INDEX_SEP)]
            if len(species) == 3:
                # NOTE Here species1 is the pivot atom of the three-body like term.
                # This is different to LAMMPS, where the pivot atom is the central one!
                species = [species[1], species[0], species[2]]

            values = [
                format_gulp_value(data, data_type, indices, k, species_val_fmt) for k in keys if k != 'reaxff3_angle6'
            ]

            if fitting_data is not None:
                num_fit += sum([1 if v in fitting_data.get(data_type, {}).get(indices, []) else 0 for v in keys])
                values += ['1' if v in fitting_data.get(data_type, {}).get(indices, []) else '0' for v in keys]

            if field in arguments and isinstance(arguments[field], list):
                args = ' '.join(arguments[field])
            elif field in arguments:
                args = arguments[field](data[data_type][indices])
            else:
                args = ''

            line = ' '.join(species + values)
            lines = textwrap.wrap(line, 78)

            if len(lines) > 2:
                raise IOError('the line cannot be coerced to fit within the 80 character limit: {}'.format(line))
            elif len(lines) > 1:
                subdata.setdefault(args, []).append('{} &'.format(lines[0]))
                subdata.setdefault(args, []).append('    {}'.format(lines[1]))
            else:
                subdata.setdefault(args, []).append(line)

        for args in sorted(subdata.keys()):
            output.append(field + ' ' + args if args else field)
            output.extend(subdata[args])

    return output, num_of_variable, num_fit


def format_gulp_value(data, data_type, indices, key, species_val_fmt):
    """ some GULP specific conversions """

    if key.startswith('global.'):
        data_type, key = key.split('.')
        value = data[data_type][key]
    else:
        value = data[data_type][indices][key]

    if key == 'reaxff2_bo3':
        # If reaxff2_bo3 = 1 needs to be set to 0 for GULP since this is a dummy value
        value = 0.0 if abs(value - 1) < 1e-12 else value

    elif key == 'reaxff2_bo5':
        # If reaxff2_bo(5,n) < 0 needs to be set to 0 for GULP since this is a dummy value
        value = 0.0 if value < 0.0 else value

    elif key == 'reaxff1_radii3':
        # TODO, this wasn't part of the original script, and should be better understood
        # but without it, the energies greatly differ to LAMMPS (approx equal otherwise)
        value = 0.0 if value > 0.0 else value

    return species_val_fmt.format(value)
