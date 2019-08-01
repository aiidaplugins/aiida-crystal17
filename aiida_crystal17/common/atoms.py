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

SYMBOLS = {
    1: 'H',
    2: 'He',
    3: 'Li',
    4: 'Be',
    5: 'B',
    6: 'C',
    7: 'N',
    8: 'O',
    9: 'F',
    10: 'Ne',
    11: 'Na',
    12: 'Mg',
    13: 'Al',
    14: 'Si',
    15: 'P',
    16: 'S',
    17: 'Cl',
    18: 'Ar',
    19: 'k',
    20: 'Ca',
    21: 'Sc',
    22: 'Ti',
    23: 'v',
    24: 'Cr',
    25: 'Mn',
    26: 'Fe',
    27: 'Co',
    28: 'Ni',
    29: 'Cu',
    30: 'Zn',
    31: 'Ga',
    32: 'Ge',
    33: 'As',
    34: 'Se',
    35: 'Br',
    36: 'Kr',
    37: 'Rb',
    38: 'Sr',
    39: 'Y',
    40: 'Zr',
    41: 'Nb',
    42: 'Mo',
    43: 'Tc',
    45: 'Ru',
    46: 'Pd',
    47: 'Ag',
    48: 'Cd',
    49: 'In',
    50: 'Sn',
    51: 'Sb',
    52: 'Te',
    53: 'I',
    54: 'Xe',
    55: 'Cs',
    56: 'Ba',
    57: 'La',
    72: 'Hf',
    73: 'Ta',
    74: 'W',
    75: 'Re',
    76: 'Os',
    77: 'Ir',
    78: 'Pt',
    79: 'Au',
    80: 'Hg',
    81: 'Tl',
    82: 'Pb',
    83: 'Bi',
    84: 'Po',
    85: 'At',
    86: 'Rn',
    87: 'Fr',
    88: 'Ra',
    89: 'Ac',
    104: 'Rf',
    105: 'Db',
    106: 'Sg',
    107: 'Bh',
    108: 'Hs',
    109: 'Mt'
}

SYMBOLS_R = {v: k for k, v in SYMBOLS.items()}

NAMES = {
    1: 'Hydrogen',
    2: 'Helium',
    3: 'Lithium',
    4: 'Beryllium',
    5: 'Boron',
    6: 'Carbon',
    7: 'Nitrogen',
    8: 'Oxygen',
    9: 'Fluorine',
    10: 'Neon',
    11: 'Sodium',
    12: 'Magnesium',
    13: 'Aluminum',
    14: 'Silicon',
    15: 'Phosphorus',
    16: 'Sulfur',
    17: 'Chlorine',
    18: 'Argon',
    19: 'Potassium',
    20: 'Calcium',
    21: 'Scandium',
    22: 'Titanium',
    23: 'Vanadium',
    24: 'Chromium',
    25: 'Manganese',
    26: 'Iron',
    27: 'Cobalt',
    28: 'Nickel',
    29: 'Copper',
    30: 'Zinc',
    31: 'Gallium',
    32: 'Germanium',
    33: 'Arsenic',
    34: 'Selenium',
    35: 'Bromine',
    36: 'Krypton',
    37: 'Rubidium',
    38: 'Strontium',
    39: 'Yttrium',
    40: 'Zirconium',
    41: 'Niobium',
    42: 'Molybdenum',
    43: 'Technetium',
    44: 'Ruthenium',
    45: 'Rhodium',
    46: 'Palladium',
    47: 'Silver',
    48: 'Cadmium',
    49: 'Indium',
    50: 'Tin',
    51: 'Antimony',
    52: 'Tellurium',
    53: 'Iodine',
    54: 'Xenon',
    55: 'Cesium',
    56: 'Barium',
    57: 'Lanthanum',
    58: 'Cerium',
    59: 'Praseodymium',
    60: 'Neodymium',
    61: 'Promethium',
    62: 'Samarium',
    63: 'Europium',
    64: 'Gadolinium',
    65: 'Terbium',
    66: 'Dysprosium',
    67: 'Holmium',
    68: 'Erbium',
    69: 'Thulium',
    70: 'Ytterbium',
    71: 'Lutetium',
    72: 'Hafnium',
    73: 'Tantalum',
    74: 'Tungsten',
    75: 'Rhenium',
    76: 'Osmium',
    77: 'Iridium',
    78: 'Platinum',
    79: 'Gold',
    80: 'Mercury',
    81: 'Thallium',
    82: 'Lead',
    83: 'Bismuth',
    84: 'Polonium',
    85: 'Astatine',
    86: 'Radon',
    87: 'Francium',
    88: 'Radium',
    89: 'Actinium',
    90: 'Thorium',
    91: 'Protactinium',
    92: 'Uranium',
    93: 'Neptunium',
    94: 'Plutonium',
    95: 'Americium',
    96: 'Curium',
    97: 'Berkelium',
    98: 'Californium',
    99: 'Einsteinium',
    100: 'Fermium',
    101: 'Mendelevium',
    102: 'Nobelium',
    103: 'Lawrencium',
    104: 'Rutherfordium',
    105: 'Dubnium',
    106: 'Seaborgium',
    107: 'Bohrium',
    108: 'Hassium',
    109: 'Meitnerium',
    110: 'Darmstadtium',
    111: 'Roentgenium',
    112: 'Copernium',
    113: 'Nihonium',
    114: 'Flerovium',
    115: 'Moscovium',
    116: 'Livermorium',
    117: 'Tennessine',
    118: 'Oganesson'
}

GAUSSIAN_ORBITALS = OrderedDict((('S', 1), ('P', 3), ('SP', 4), ('D', 5), ('F', 7)))  # TODO G

ELECTRON_CONFIGURATIONS = {
    1: {
        'inner': None,
        'outer': (('1s', 1),)
    },
    2: {
        'inner': None,
        'outer': (('1s', 2),)
    },
    3: {
        'inner': 2,
        'outer': (('2s', 1),)
    },
    4: {
        'inner': 2,
        'outer': (('2s', 2),)
    },
    5: {
        'inner': 2,
        'outer': (('2s', 2), ('2p', 1))
    },
    6: {
        'inner': 2,
        'outer': (('2s', 2), ('2p', 2))
    },
    7: {
        'inner': 2,
        'outer': (('2s', 2), ('2p', 3))
    },
    8: {
        'inner': 2,
        'outer': (('2s', 2), ('2p', 4))
    },
    9: {
        'inner': 2,
        'outer': (('2s', 2), ('2p', 5))
    },
    10: {
        'inner': 2,
        'outer': (('2s', 2), ('2p', 6))
    },
    11: {
        'inner': 10,
        'outer': (('3s', 1),)
    },
    12: {
        'inner': 10,
        'outer': (('3s', 2),)
    },
    13: {
        'inner': 10,
        'outer': (('3s', 2), ('3p', 1))
    },
    14: {
        'inner': 10,
        'outer': (('3s', 2), ('3p', 2))
    },
    15: {
        'inner': 10,
        'outer': (('3s', 2), ('3p', 3))
    },
    16: {
        'inner': 10,
        'outer': (('3s', 2), ('3p', 4))
    },
    17: {
        'inner': 10,
        'outer': (('3s', 2), ('3p', 5))
    },
    18: {
        'inner': 10,
        'outer': (('3s', 2), ('3p', 6))
    },
    19: {
        'inner': 18,
        'outer': (('4s', 1),)
    },
    20: {
        'inner': 18,
        'outer': (('4s', 2),)
    },
    21: {
        'inner': 18,
        'outer': (('3d', 1), ('4s', 2))
    },
    22: {
        'inner': 18,
        'outer': (('3d', 2), ('4s', 2))
    },
    23: {
        'inner': 18,
        'outer': (('3d', 3), ('4s', 2))
    },
    24: {
        'inner': 18,
        'outer': (('3d', 5), ('4s', 1))
    },
    25: {
        'inner': 18,
        'outer': (('3d', 5), ('4s', 2))
    },
    26: {
        'inner': 18,
        'outer': (('3d', 6), ('4s', 2))
    },
    27: {
        'inner': 18,
        'outer': (('3d', 7), ('4s', 2))
    },
    28: {
        'inner': 18,
        'outer': (('3d', 8), ('4s', 2))
    },
    29: {
        'inner': 18,
        'outer': (('3d', 10), ('4s', 1))
    },
    30: {
        'inner': 18,
        'outer': (('3d', 10), ('4s', 2))
    },
    31: {
        'inner': 18,
        'outer': (('3d', 10), ('4s', 2), ('4p', 1))
    },
    32: {
        'inner': 18,
        'outer': (('3d', 10), ('4s', 2), ('4p', 2))
    },
    33: {
        'inner': 18,
        'outer': (('3d', 10), ('4s', 2), ('4p', 3))
    },
    34: {
        'inner': 18,
        'outer': (('3d', 10), ('4s', 2), ('4p', 4))
    },
    35: {
        'inner': 18,
        'outer': (('3d', 10), ('4s', 2), ('4p', 5))
    },
    36: {
        'inner': 18,
        'outer': (('3d', 10), ('4s', 2), ('4p', 6))
    },
    37: {
        'inner': 36,
        'outer': (('5s', 1),)
    },
    38: {
        'inner': 36,
        'outer': (('5s', 2),)
    },
    39: {
        'inner': 36,
        'outer': (('4d', 1), ('5s', 2))
    },
    40: {
        'inner': 36,
        'outer': (('4d', 2), ('5s', 2))
    },
    41: {
        'inner': 36,
        'outer': (('4d', 4), ('5s', 1))
    },
    42: {
        'inner': 36,
        'outer': (('4d', 5), ('5s', 1))
    },
    43: {
        'inner': 36,
        'outer': (('4d', 5), ('5s', 2))
    },
    44: {
        'inner': 36,
        'outer': (('4d', 7), ('5s', 1))
    },
    45: {
        'inner': 36,
        'outer': (('4d', 8), ('5s', 1))
    },
    46: {
        'inner': 36,
        'outer': (('4d', 10),)
    },
    47: {
        'inner': 36,
        'outer': (('4d', 10), ('5s', 1))
    },
    48: {
        'inner': 36,
        'outer': (('4d', 10), ('5s', 2))
    },
    49: {
        'inner': 36,
        'outer': (('4d', 10), ('5s', 2), ('5p', 1))
    },
    50: {
        'inner': 36,
        'outer': (('4d', 10), ('5s', 2), ('5p', 2))
    },
    51: {
        'inner': 36,
        'outer': (('4d', 10), ('5s', 2), ('5p', 3))
    },
    52: {
        'inner': 36,
        'outer': (('4d', 10), ('5s', 2), ('5p', 4))
    },
    53: {
        'inner': 36,
        'outer': (('4d', 10), ('5s', 2), ('5p', 5))
    },
    54: {
        'inner': 36,
        'outer': (('4d', 10), ('5s', 2), ('5p', 6))
    },
    55: {
        'inner': 54,
        'outer': (('6s', 1),)
    },
    56: {
        'inner': 54,
        'outer': (('6s', 2),)
    },
    57: {
        'inner': 54,
        'outer': (('5d', 1), ('6s', 2))
    },
    58: {
        'inner': 54,
        'outer': (('4f', 1), ('5d', 1), ('6s', 2))
    },
    59: {
        'inner': 54,
        'outer': (('4f', 3), ('6s', 2))
    },
    60: {
        'inner': 54,
        'outer': (('4f', 4), ('6s', 2))
    },
    61: {
        'inner': 54,
        'outer': (('4f', 5), ('6s', 2))
    },
    62: {
        'inner': 54,
        'outer': (('4f', 6), ('6s', 2))
    },
    63: {
        'inner': 54,
        'outer': (('4f', 7), ('6s', 2))
    },
    64: {
        'inner': 54,
        'outer': (('4f', 7), ('5d', 1), ('6s', 2))
    },
    65: {
        'inner': 54,
        'outer': (('4f', 9), ('6s', 2))
    },
    66: {
        'inner': 54,
        'outer': (('4f', 10), ('6s', 2))
    },
    67: {
        'inner': 54,
        'outer': (('4f', 11), ('6s', 2))
    },
    68: {
        'inner': 54,
        'outer': (('4f', 12), ('6s', 2))
    },
    69: {
        'inner': 54,
        'outer': (('4f', 13), ('6s', 2))
    },
    70: {
        'inner': 54,
        'outer': (('4f', 14), ('6s', 2))
    },
    71: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 1), ('6s', 2))
    },
    72: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 2), ('6s', 2))
    },
    73: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 3), ('6s', 2))
    },
    74: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 4), ('6s', 2))
    },
    75: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 5), ('6s', 2))
    },
    76: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 6), ('6s', 2))
    },
    77: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 7), ('6s', 2))
    },
    78: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 9), ('6s', 1))
    },
    79: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 10), ('6s', 1))
    },
    80: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 10), ('6s', 2))
    },
    81: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 10), ('6s', 2), ('6p', 1))
    },
    82: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 10), ('6s', 2), ('6p', 2))
    },
    83: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 10), ('6s', 2), ('6p', 3))
    },
    84: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 10), ('6s', 2), ('6p', 4))
    },
    85: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 10), ('6s', 2), ('6p', 5))
    },
    86: {
        'inner': 54,
        'outer': (('4f', 14), ('5d', 10), ('6s', 2), ('6p', 6))
    },
    87: {
        'inner': 86,
        'outer': (('7s', 1),)
    },
    88: {
        'inner': 86,
        'outer': (('7s', 2),)
    },
    89: {
        'inner': 86,
        'outer': (('6d', 1), ('7s', 2))
    },
    90: {
        'inner': 86,
        'outer': (('6d', 2), ('7s', 2))
    },
    91: {
        'inner': 86,
        'outer': (('5f', 2), ('6d', 1), ('7s', 2))
    },
    92: {
        'inner': 86,
        'outer': (('5f', 3), ('6d', 1), ('7s', 2))
    },
    93: {
        'inner': 86,
        'outer': (('5f', 4), ('6d', 1), ('7s', 2))
    },
    94: {
        'inner': 86,
        'outer': (('5f', 6), ('7s', 2))
    },
    95: {
        'inner': 86,
        'outer': (('5f', 7), ('7s', 2))
    },
    96: {
        'inner': 86,
        'outer': (('5f', 7), ('6d', 1), ('7s', 2))
    },
    97: {
        'inner': 86,
        'outer': (('5f', 9), ('7s', 2))
    },
    98: {
        'inner': 86,
        'outer': (('5f', 10), ('7s', 2))
    },
    99: {
        'inner': 86,
        'outer': (('5f', 11), ('7s', 2))
    },
    100: {
        'inner': 86,
        'outer': (('5f', 12), ('7s', 2))
    },
    101: {
        'inner': 86,
        'outer': (('5f', 13), ('7s', 2))
    },
    102: {
        'inner': 86,
        'outer': (('5f', 14), ('7s', 2))
    },
    103: {
        'inner': 86,
        'outer': (('5f', 14), ('7s', 2), ('7p', 1))
    },
    104: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 2), ('7s', 2))
    },
    105: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 3), ('7s', 2))
    },
    106: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 4), ('7s', 2))
    },
    107: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 5), ('7s', 2))
    },
    108: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 6), ('7s', 2))
    },
    109: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 7), ('7s', 2))
    },
    110: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 9), ('7s', 1))
    },
    111: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 10), ('7s', 1))
    },
    112: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 10), ('7s', 2))
    },
    113: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 10), ('7s', 2), ('7p', 1))
    },
    114: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 10), ('7s', 2), ('7p', 2))
    },
    115: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 10), ('7s', 2), ('7p', 3))
    },
    116: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 10), ('7s', 2), ('7p', 4))
    },
    117: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 10), ('7s', 2), ('7p', 5))
    },
    118: {
        'inner': 86,
        'outer': (('5f', 14), ('6d', 10), ('7s', 2), ('7p', 6))
    }
}
