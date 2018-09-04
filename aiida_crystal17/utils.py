"""
helpful code
"""
import collections
from jsonextended import edict

# python 3 to 2 compatibility
try:
    basestring
except NameError:
    basestring = str  # pylint: disable=redefined-builtin


def unflatten_dict(indict, delimiter="."):
    return edict.unflatten(indict, key_as_tuple=False, delim=delimiter)


def flatten_dict(indict, delimiter="."):
    return edict.flatten(indict, key_as_tuple=False, sep=delimiter)


class HelpDict(collections.MutableMapping):
    """a dictionary which associates help text with each key"""

    def __init__(self, *args, **kwargs):
        self._store = dict()
        self._help = {}
        for key, val in dict(*args, **kwargs).items():
            self[key] = val

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        assert isinstance(key, basestring)
        if not isinstance(value, tuple):
            self._store[key] = value[0]
            self._help[key] = ''
        else:
            if len(value) != 2 or not isinstance(value[1], basestring):
                raise AssertionError(
                    "the value must be a tuple of form (val, help_string)")
            self._store[key] = value[0]
            self._help[key] = value[1]

    def __delitem__(self, key):
        del self._help[key]
        del self._store[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def _get_help(self):
        return self._help.copy()

    help = property(_get_help)

    def __repr__(self):
        rep = "{\n"

        rep += ",\n".join([
            "  '{0}': {1} [{2}]".format(key, self._store[key], self._help[key])
            for key in self
        ])
        rep += "\n}"
        return rep

    def copy(self):
        return HelpDict({k: (self._store[k], self._help[k]) for k in self})


ATOMIC_NUM2SYMBOL = {
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

ATOMIC_SYMBOL2NUM = {v: k for k, v in ATOMIC_NUM2SYMBOL.items()}
