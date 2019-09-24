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
"""Parse gaussian cube file data to a VESTA input file."""
from collections import namedtuple
import io
import os
import shutil
from textwrap import dedent

import ase
import six

from aiida_crystal17.parsers.raw.gaussian_cube import read_gaussian_cube
from aiida_crystal17.validation import validate_against_schema

SymbolInfo = namedtuple('SymbolInfo', ['radius', 'r2', 'r3', 'r', 'g', 'b'])


def get_default_settings():
    """Return dict of default settings."""
    return {
        'bounds': {
            'xmin': 0,
            'xmax': 1,
            'ymin': 0,
            'ymax': 1,
            'zmin': 0,
            'zmax': 1,
        },
        'iso_surfaces': [
            [0.1, 1, 1, 1, 0, 0.7845, 0.7845],
            [0.05, 1, 0.071, 1, 0.216, 0.5883, 0.5883],
            [0.025, 1, 0.0510, 1, 0.9648, 0.1178, 0.1178],
        ],
        'bonds': [],
        'show_compass': True,
        '2d_display': {
            'h': 1e-06,
            'k': 1e-06,
            'l': 1,
            'dist_from_o': 0.0001,
            'fill_min': 0.0,
            'fill_max': 0.1,
            'contour_interval': 0.01,
            'contour_min': 0.0,
            'contour_max': 0.1,
            'contour_width1': 0.01,
            'contour_width2': 0.01,
            'bound_width': 1,
            'xmin': -0.5,
            'xmax': 1.5,
            'ymin': -0.5,
            'ymax': 1.5,
            'zmin': -0.5,
            'zmax': 1.5,
            'zscale': 100000.0
        },
    }


def get_complete_settings(settings):
    """Merge any user defined settings with the default dict."""
    defaults = get_default_settings()
    if not settings:
        return defaults
    for key in settings:
        if key in defaults and isinstance(defaults[key], dict):
            if not isinstance(settings[key], dict):
                raise ValueError("Settings key '{}' should be a dict".format(key))
            defaults[key].update(settings[key])
        elif key in defaults:
            defaults[key] = settings[key]
        else:
            raise KeyError('settings contains an unrecognised key: {}'.format(key))
    return defaults


def create_vesta_input(cube_data, cube_filepath, settings=None):
    """Return the file content of a VESTA input file.

    Parameters
    ----------
    cube_data: aiida_crystal17.parsers.raw.gaussian_cube.GcubeResult
    cube_filepath: str
    settings: dict
        Settings that will be merged with the default settings,
        and validated against 'vesta_input.schema.json'

    Returns
    -------
    str

    """
    settings = get_complete_settings(settings)
    validate_against_schema(settings, 'vesta_input.schema.json')
    for dim in ('x', 'y', 'z'):
        if not settings['bounds'][dim + 'min'] < settings['bounds'][dim + 'max']:
            raise ValueError('bounds: {}min must be less than {}max'.format(dim))
        if not settings['2d_display'][dim + 'min'] < settings['2d_display'][dim + 'max']:
            raise ValueError('2d_display: {}min must be less than {}max'.format(dim))

    atoms = ase.Atoms(
        cell=cube_data.cell,
        positions=cube_data.atoms_positions,
        numbers=cube_data.atoms_atomic_number,
        pbc=True,
    )
    el_info = {s: SymbolInfo(*VESTA_ELEMENT_INFO[s]) for s in set(atoms.get_chemical_symbols())}

    # header
    lines = [
        '#VESTA_FORMAT_VERSION 3.3.0',
        '',
        'CRYSTAL',
        '',
        'TITLE',
        ''
        # NB: originally used cube_data.header[0],
        # but the file load can fail if a key word (like CRYSTAL) is in the title
        'GAUSSIAN_CUBE_DATA',
        '',
    ]

    # density input
    lines.extend(['IMPORT_DENSITY 1', '+1.000000 {}'.format(cube_filepath), ''])

    # symmetry
    lines.extend([
        'GROUP',
        '1 1 P 1',
        'SYMOP',
        '0.000000  0.000000  0.000000  1  0  0   0  1  0   0  0  1   1',
        '-1.0 -1.0 -1.0  0 0 0  0 0 0  0 0 0',
    ])

    # position and orientation (hard-coded)
    # LORIENT:
    #    <this plane h, k, l> <global h, k, l>
    #    <this plane u, v, w> <global u, v, w>
    lines.extend(
        dedent("""\
        TRANM 0
          0.000000  0.000000  0.000000  1  0  0   0  1  0   0  0  1
        LTRANSL
          -1
          0.000000  0.000000  0.000000  0.000000  0.000000  0.000000
        LORIENT
          -1   0   0   0   0
          1.000000  0.000000  0.000000  1.000000  0.000000  0.000000
          0.000000  0.000000  1.000000  0.000000  0.000000  1.000000
        LMATRIX
          1.000000  0.000000  0.000000  0.000000
          0.000000  1.000000  0.000000  0.000000
          0.000000  0.000000  1.000000  0.000000
          0.000000  0.000000  0.000000  1.000000
          0.000000  0.000000  0.000000""").splitlines())

    # cell parameters
    lines.extend([
        'CELLP',
        '  {:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f}'.format(*atoms.get_cell_lengths_and_angles()),
        '  0.000000   0.000000   0.000000   0.000000   0.000000   0.000000',
    ])

    # atomic sites
    lines.append('STRUC')
    for i, ((x, y, z), symbol) in enumerate(zip(atoms.get_scaled_positions(),
                                                atoms.get_chemical_symbols())):  # type: (int, ase.Atom)
        lines.append('  {idx:<2d} {sym:<2s} {sym:>2s}{idx:<2d} {occ:.6f} {x:.6f} {y:.6f} {z:.6f} {wyck} -'.format(
            idx=i + 1, sym=symbol, occ=1.0, x=x, y=y, z=z, wyck='1'))
        lines.append('    0.000000   0.000000   0.000000  0.00')
    lines.append('  0 0 0 0 0 0 0')

    # isotropic displacement parameter
    lines.append('THERI 0')
    for i, atom in enumerate(atoms):  # type: (int, ase.Atom)
        lines.append('  {idx:<2d} {sym:>2s}{idx:<2d}  1.000000'.format(idx=i + 1, sym=atom.symbol))
    lines.append('  0 0 0')

    lines.extend(['SHAPE', '  0       0       0       0   0.000000  0   192   192   192   192'])

    # repeat unit cell
    lines.extend([
        'BOUND',
        '  {xmin:.6f} {xmax:.6f} {ymin:.6f} {ymax:.6f} {zmin:.6f} {zmax:.6f}'.format(**settings['bounds']),
        '  0   0   0   0  0',
    ])

    # neighbour bonds
    lines.append('SBOND')
    for i, (sym1, sym2, minr, maxr) in enumerate(settings['bonds']):
        lines.append(
            '  {idx:<2d} {sym1:<2s} {sym2:<2s} {minr:.6f} {maxr:.6f} 0  1  1  0  1 {rad:.3f} 1.000 180 180 180'.format(
                idx=i + 1, sym1=sym1, sym2=sym2, minr=minr, maxr=maxr, rad=0.25))
    lines.append('  0 0 0 0')

    # site radii and colors
    # TODO allow bespoke site colors
    lines.append('SITET')
    lines.extend([
        '  {idx:<2d} {sym:>2s}{idx:<2d} {rad:.6f} {r} {g} {b} {r} {g} {b}  100  0'.format(
            idx=i + 1,
            sym=a.symbol,
            rad=el_info[a.symbol].radius,
            r=int(el_info[a.symbol].r * 255),
            g=int(el_info[a.symbol].g * 255),
            b=int(el_info[a.symbol].b * 255),
        ) for i, a in enumerate(atoms)
    ])
    lines.append('  0 0 0 0 0 0')

    # additional lines (currently hardcoded)
    lines.extend([
        'VECTR',
        ' 0 0 0 0 0',
        'VECTT',
        ' 0 0 0 0 0',
        'SPLAN',
        '  0   0   0   0',
        'LBLAT',
        ' -1',
        'LBLSP',
        ' -1',
        'DLATM',
        ' -1',
        'DLBND',
        ' -1',
        'DLPLY',
        ' -1',
    ])

    # 2D data display
    lines.extend(
        dedent("""\
        PLN2D
          1  {h:.6E} {k:.6E} {l:.6E} {dist_from_o:.6E} 1.0000 255 255 255 255
         1 96 {birds_eye} {fill_min:.6E} {fill_max:.6E}
         {contour_interval:.6E} {contour_min:.6E} {contour_max:.6E} 1 10 -1 2 5
         {bound_width:.6f} {contour_width1:.6f} {contour_width2:.6f} {zscale:.6E}
         {xmin:.6f} {xmax:.6f} {ymin:.6f} {ymax:.6f} {zmin:.6f} {zmax:.6f}
         0.500000  0.500000  0.500000  1.000000
        """).format(birds_eye='0', **settings['2d_display']).splitlines())
    # translation and zoom (hard-coded)
    lines.append(' 0 0 0 1')
    # line colors and orientation (hard-coded)
    lines.extend(
        dedent("""\
            255 255 255
             0   0   0
             0   0   0
             0   0   0
            1.000000  0.000000  0.000000  0.000000
            0.000000  1.000000  0.000000  0.000000
            0.000000  0.000000  1.000000  0.000000
            0.000000  0.000000  0.000000  1.000000
            0   0   0   0""").splitlines())

    # element radii and colors
    lines.append('ATOMT')
    lines.extend([
        '  {idx:<2d} {sym:<2s} {rad:.6f} {r} {g} {b} {r} {g} {b} 100'.format(
            idx=i + 1,
            sym=s,
            rad=el_info[s].radius,
            r=int(el_info[s].r * 255),
            g=int(el_info[s].g * 255),
            b=int(el_info[s].b * 255),
        ) for i, s in enumerate(sorted(set(atoms.get_chemical_symbols())))
    ])
    lines.append('  0 0 0 0 0 0')

    # initial scene orientation (hard-coded)
    lines.extend(
        dedent("""\
            SCENE
            1.000000  0.000000  0.000000  0.000000
            0.000000  1.000000  0.000000  0.000000
            0.000000  0.000000  1.000000  0.000000
            0.000000  0.000000  0.000000  1.000000
            0.000   0.000
            0.000
            1.000
            HBOND 0 2

            """).splitlines())

    # style section
    # TODO make options variable
    lines.extend(
        dedent("""\
            STYLE
            DISPF 147551
            MODEL   0  1  0
            SURFS   0  1  1
            SECTS  96  0
            FORMS   0  1
            ATOMS   0  0  1
            BONDS   1
            POLYS   1
            VECTS 1.000000
            FORMP
              1  1.0   0   0   0
            ATOMP
              24  24   0  50  2.0   0
            BONDP
              1  16  0.250  1.000 180 180 180
            POLYP
              100 1  1.000 180 180 180""").splitlines())

    # isosurfaces
    lines.append('ISURF')
    lines.extend([('  {idx:<2d} {pos_neg:d} {val:.6f} '
                   '{r:3d} {g:3d} {b:3d} {a1:3d} {a2:3d}').format(idx=i + 1,
                                                                  val=val,
                                                                  pos_neg=pos_neg,
                                                                  r=int(r * 255),
                                                                  g=int(g * 255),
                                                                  b=int(b * 255),
                                                                  a1=int(a1 * 255),
                                                                  a2=int(a2 * 255))
                  for i, (val, pos_neg, r, g, b, a1, a2) in enumerate(settings['iso_surfaces'])])
    lines.append('  0   0   0   0')

    # final settings
    lines.extend(
        dedent("""\
            TEX3P
              1  0.00000E+00  1.00000E+00
            SECTP
              1  5.00000E-01  5.00000E-01  0.00000E+00
            HKLPP
              192 1  1.000 255   0 255
            UCOLP
              1   1  1.000   0   0   0
            COMPS {compass}
              LABEL 1    12  1.000 0
            PROJT 0  0.962
            BKGRC
              255 255 255
            DPTHQ 1 -0.5000  3.5000
            LIGHT0 1
              1.000000  0.000000  0.000000  0.000000
              0.000000  1.000000  0.000000  0.000000
              0.000000  0.000000  1.000000  0.000000
              0.000000  0.000000  0.000000  1.000000
              0.000000  0.000000 20.000000  0.000000
              0.000000  0.000000 -1.000000
              26  26  26 255
              179 179 179 255
              255 255 255 255
            LIGHT1
              1.000000  0.000000  0.000000  0.000000
              0.000000  1.000000  0.000000  0.000000
              0.000000  0.000000  1.000000  0.000000
              0.000000  0.000000  0.000000  1.000000
              0.000000  0.000000 20.000000  0.000000
              0.000000  0.000000 -1.000000
              0   0   0   0
              0   0   0   0
              0   0   0   0
            LIGHT2
              1.000000  0.000000  0.000000  0.000000
              0.000000  1.000000  0.000000  0.000000
              0.000000  0.000000  1.000000  0.000000
              0.000000  0.000000  0.000000  1.000000
              0.000000  0.000000 20.000000  0.000000
              0.000000  0.000000 -1.000000
              0   0   0   0
              0   0   0   0
              0   0   0   0
            LIGHT3
              1.000000  0.000000  0.000000  0.000000
              0.000000  1.000000  0.000000  0.000000
              0.000000  0.000000  1.000000  0.000000
              0.000000  0.000000  0.000000  1.000000
              0.000000  0.000000 20.000000  0.000000
              0.000000  0.000000 -1.000000
              0   0   0   0
              0   0   0   0
              0   0   0   0
            ATOMM
              204 204 204 255
              25.600
            BONDM
              255 255 255 255
              128.000
            POLYM
              255 255 255 255
              128.000
            SURFM
              0   0   0 255
              128.000
            FORMM
              255 255 255 255
              128.000
            HKLPM
              255 255 255 255
              128.000

            """.format(compass=1 if settings['show_compass'] else 0)).splitlines())

    return '\n'.join(lines)


def write_vesta_files(
        aiida_gcube,
        folder_path,
        file_name,
        settings=None,
):
    """Use an ``crystal17.gcube`` data node to create the input files for VESTA.

    Parameters
    ----------
    aiida_gcube: aiida_crystal17.data.gcube.GaussianCube
    folder_path: str
    file_name: str
        The name of the files (without extension) to write
    settings: dict
        Settings that will be merged with the default settings,
        and validated against 'vesta_input.schema.json'

    """
    cube_filepath = os.path.join(folder_path, '{}.cube'.format(file_name))
    vesta_filepath = os.path.join(folder_path, '{}.vesta'.format(file_name))
    with aiida_gcube.open_cube_file() as handle:
        cube_data = read_gaussian_cube(handle, return_density=False, dist_units='angstrom')
        content = create_vesta_input(cube_data, os.path.basename(cube_filepath), settings=settings)
        with io.open(vesta_filepath, 'w') as out_handle:
            out_handle.write(six.ensure_text(content))
    with aiida_gcube.open_cube_file(binary=True) as handle:
        with io.open(cube_filepath, 'wb') as out_handle:
            shutil.copyfileobj(handle, out_handle)


VESTA_ELEMENT_INFO = {
    'H': (0.46, 1.2, 0.2, 1.0, 0.8, 0.8),
    'D': (0.46, 1.2, 0.2, 0.8, 0.8, 1.0),
    'He': (1.22, 1.4, 1.22, 0.98907, 0.91312, 0.81091),
    'Li': (1.57, 1.4, 0.59, 0.52731, 0.87953, 0.4567),
    'Be': (1.12, 1.4, 0.27, 0.37147, 0.8459, 0.48292),
    'B': (0.81, 1.4, 0.11, 0.1249, 0.63612, 0.05948),
    'C': (0.77, 1.7, 0.15, 0.5043, 0.28659, 0.16236),
    'N': (0.74, 1.55, 1.46, 0.69139, 0.72934, 0.9028),
    'O': (0.74, 1.52, 1.4, 0.99997, 0.01328, 0.0),
    'F': (0.72, 1.47, 1.33, 0.69139, 0.72934, 0.9028),
    'Ne': (1.6, 1.54, 1.6, 0.99954, 0.21788, 0.71035),
    'Na': (1.91, 1.54, 1.02, 0.97955, 0.86618, 0.23787),
    'Mg': (1.6, 1.54, 0.72, 0.98773, 0.48452, 0.0847),
    'Al': (1.43, 1.54, 0.39, 0.50718, 0.70056, 0.84062),
    'Si': (1.18, 2.1, 0.26, 0.10596, 0.23226, 0.98096),
    'P': (1.1, 1.8, 0.17, 0.75557, 0.61256, 0.76425),
    'S': (1.04, 1.8, 1.84, 1.0, 0.98071, 0.0),
    'Cl': (0.99, 1.75, 1.81, 0.19583, 0.98828, 0.01167),
    'Ar': (1.92, 1.88, 1.92, 0.81349, 0.99731, 0.77075),
    'K': (2.35, 1.88, 1.51, 0.63255, 0.13281, 0.96858),
    'Ca': (1.97, 1.88, 1.12, 0.35642, 0.58863, 0.74498),
    'Sc': (1.64, 1.88, 0.745, 0.71209, 0.3893, 0.67279),
    'Ti': (1.47, 1.88, 0.605, 0.47237, 0.79393, 1.0),
    'V': (1.35, 1.88, 0.58, 0.9, 0.1, 0.0),
    'Cr': (1.29, 1.88, 0.615, 0.0, 0.0, 0.62),
    'Mn': (1.37, 1.88, 0.83, 0.66148, 0.03412, 0.62036),
    'Fe': (1.26, 1.88, 0.78, 0.71051, 0.44662, 0.00136),
    'Co': (1.25, 1.88, 0.745, 0.0, 0.0, 0.68666),
    'Ni': (1.25, 1.88, 0.69, 0.72032, 0.73631, 0.74339),
    'Cu': (1.28, 1.88, 0.73, 0.1339, 0.28022, 0.86606),
    'Zn': (1.37, 1.88, 0.74, 0.56123, 0.56445, 0.50799),
    'Ga': (1.53, 1.88, 0.62, 0.62292, 0.89293, 0.45486),
    'Ge': (1.22, 1.88, 0.53, 0.49557, 0.43499, 0.65193),
    'As': (1.21, 1.85, 0.335, 0.45814, 0.81694, 0.34249),
    'Se': (1.04, 1.9, 1.98, 0.6042, 0.93874, 0.06122),
    'Br': (1.14, 1.85, 1.96, 0.49645, 0.19333, 0.01076),
    'Kr': (1.98, 2.02, 1.98, 0.98102, 0.75805, 0.95413),
    'Rb': (2.5, 2.02, 1.61, 1.0, 0.0, 0.6),
    'Sr': (2.15, 2.02, 1.26, 0.0, 1.0, 0.15259),
    'Y': (1.82, 2.02, 1.019, 0.40259, 0.59739, 0.55813),
    'Zr': (1.6, 2.02, 0.72, 0.0, 1.0, 0.0),
    'Nb': (1.47, 2.02, 0.64, 0.29992, 0.70007, 0.46459),
    'Mo': (1.4, 2.02, 0.59, 0.70584, 0.52602, 0.68925),
    'Tc': (1.35, 2.02, 0.56, 0.80574, 0.68699, 0.79478),
    'Ru': (1.34, 2.02, 0.62, 0.81184, 0.72113, 0.68089),
    'Rh': (1.34, 2.02, 0.665, 0.80748, 0.82205, 0.67068),
    'Pd': (1.37, 2.02, 0.86, 0.75978, 0.76818, 0.72454),
    'Ag': (1.44, 2.02, 1.15, 0.72032, 0.73631, 0.74339),
    'Cd': (1.52, 2.02, 0.95, 0.95145, 0.12102, 0.86354),
    'In': (1.67, 2.02, 0.8, 0.84378, 0.50401, 0.73483),
    'Sn': (1.58, 2.02, 0.69, 0.60764, 0.56052, 0.72926),
    'Sb': (1.41, 2.0, 0.76, 0.84627, 0.51498, 0.31315),
    'Te': (1.37, 2.06, 2.21, 0.67958, 0.63586, 0.32038),
    'I': (1.33, 1.98, 2.2, 0.55914, 0.122, 0.54453),
    'Xe': (2.18, 2.16, 0.48, 0.60662, 0.63218, 0.97305),
    'Cs': (2.72, 2.16, 1.74, 0.05872, 0.99922, 0.72578),
    'Ba': (2.24, 2.16, 1.42, 0.11835, 0.93959, 0.17565),
    'La': (1.88, 2.16, 1.16, 0.3534, 0.77057, 0.28737),
    'Ce': (1.82, 2.16, 0.97, 0.82055, 0.99071, 0.02374),
    'Pr': (1.82, 2.16, 1.126, 0.9913, 0.88559, 0.02315),
    'Nd': (1.82, 2.16, 1.109, 0.98701, 0.5556, 0.02744),
    'Pm': (1.81, 2.16, 1.093, 0.0, 0.0, 0.96),
    'Sm': (1.81, 2.16, 1.27, 0.99042, 0.02403, 0.49195),
    'Eu': (2.06, 2.16, 1.066, 0.98367, 0.03078, 0.83615),
    'Gd': (1.79, 2.16, 1.053, 0.75325, 0.01445, 1.0),
    'Tb': (1.77, 2.16, 1.04, 0.44315, 0.01663, 0.99782),
    'Dy': (1.77, 2.16, 1.027, 0.1939, 0.02374, 0.99071),
    'Ho': (1.76, 2.16, 1.015, 0.02837, 0.25876, 0.98608),
    'Er': (1.75, 2.16, 1.004, 0.28688, 0.45071, 0.23043),
    'Tm': (1.0, 2.16, 0.994, 0.0, 0.0, 0.88),
    'Yb': (1.94, 2.16, 0.985, 0.15323, 0.99165, 0.95836),
    'Lu': (1.72, 2.16, 0.977, 0.15097, 0.99391, 0.71032),
    'Hf': (1.59, 2.16, 0.71, 0.70704, 0.70552, 0.3509),
    'Ta': (1.47, 2.16, 0.64, 0.71952, 0.60694, 0.33841),
    'W': (1.41, 2.16, 0.6, 0.55616, 0.54257, 0.50178),
    'Re': (1.37, 2.16, 0.53, 0.70294, 0.69401, 0.55789),
    'Os': (1.35, 2.16, 0.63, 0.78703, 0.69512, 0.47379),
    'Ir': (1.36, 2.16, 0.625, 0.78975, 0.81033, 0.45049),
    'Pt': (1.39, 2.16, 0.625, 0.79997, 0.77511, 0.75068),
    'Au': (1.44, 2.16, 1.37, 0.99628, 0.70149, 0.22106),
    'Hg': (1.55, 2.16, 1.02, 0.8294, 0.72125, 0.79823),
    'Tl': (1.71, 2.16, 0.885, 0.58798, 0.53854, 0.42649),
    'Pb': (1.75, 2.16, 1.19, 0.32386, 0.32592, 0.35729),
    'Bi': (1.82, 2.16, 1.03, 0.82428, 0.18732, 0.97211),
    'Po': (1.77, 2.16, 0.94, 0.0, 0.0, 1.0),
    'At': (0.62, 2.16, 0.62, 0.0, 0.0, 1.0),
    'Rn': (0.8, 2.16, 0.8, 1.0, 1.0, 0.0),
    'Fr': (1.0, 2.16, 1.8, 0.0, 0.0, 0.0),
    'Ra': (2.35, 2.16, 1.48, 0.42959, 0.66659, 0.34786),
    'Ac': (2.03, 2.16, 1.12, 0.39344, 0.62101, 0.45034),
    'Th': (1.8, 2.16, 1.05, 0.14893, 0.99596, 0.47106),
    'Pa': (1.63, 2.16, 0.78, 0.16101, 0.98387, 0.20855),
    'U': (1.56, 2.16, 0.73, 0.47774, 0.63362, 0.66714),
    'Np': (1.56, 2.16, 0.75, 0.3, 0.3, 0.3),
    'Pu': (1.64, 2.16, 0.86, 0.3, 0.3, 0.3),
    'Am': (1.73, 2.16, 0.975, 0.3, 0.3, 0.3),
    'XX': (0.8, 1.0, 0.8, 0.3, 0.3, 0.3),
}
