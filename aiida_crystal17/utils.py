"""
helpful code
"""
from packaging import version
import collections
from jsonextended import edict

# python 3 to 2 compatibility
try:
    basestring
except NameError:
    basestring = str  # pylint: disable=redefined-builtin


def aiida_version():
    """get the version of aiida in use

    :returns: packaging.version.Version
    """
    from aiida import __version__ as aiida_version_
    return version.parse(aiida_version_)


def cmp_version(string):
    """convert a version string to a packaging.version.Version"""
    return version.parse(string)


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


def get_keys(dct, keys, default=None, raise_error=False):
    """retrieve the leaf of a key path from a dictionary

    :param dct: the dict to search
    :param keys: key path
    :param default: default value to return
    :param raise_error: whether to raise an error if the path isn't found
    :return:
    """
    subdct = dct
    for i, key in enumerate(keys):
        try:
            subdct = subdct[key]
        except (KeyError, IndexError):
            if raise_error:
                raise ValueError("could not find key path: {}".format(
                    keys[0:i + 1]))
            else:
                return default
    return subdct


def run_get_node(process, inputs_dict):
    """ an implementation of run_get_node which is compatible with both aiida v0.12 and v1.0.0

    it will also convert "options" "label" and "description" to/from the _ variant

    :param process: a process
    :param inputs_dict: a dictionary of inputs
    :type inputs_dict: dict
    :return: the calculation Node
    """
    if aiida_version() < cmp_version("1.0.0a1"):
        for key in ["options", "label", "description"]:
            if key in inputs_dict:
                inputs_dict["_" + key] = inputs_dict.pop(key)
        workchain = process.new_instance(inputs=inputs_dict)
        workchain.run_until_complete()
        calcnode = workchain.calc
    else:
        from aiida.work.launch import run_get_node  # pylint: disable=import-error
        for key in ["_options", "_label", "_description"]:
            if key in inputs_dict:
                inputs_dict[key[1:]] = inputs_dict.pop(key)
        _, calcnode = run_get_node(process, **inputs_dict)

    return calcnode
