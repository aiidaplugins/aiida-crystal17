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
