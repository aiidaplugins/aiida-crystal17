import datetime
import json
from textwrap import wrap
from jsonextended import edict
from aiida import load_profile


def unflatten_dict(indict, delimiter="."):
    return edict.unflatten(indict, key_as_tuple=False, delim=delimiter)


def flatten_dict(indict, delimiter="."):
    return edict.flatten(indict, key_as_tuple=False, sep=delimiter)


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


class BuilderEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return dict(obj)
        except TypeError:
            pass
        return wrap(str(obj))


def display_json(builder, indent=2):
    """ pretty print a dictionary object in a Jupyter Notebook """
    from IPython.display import display_markdown
    return display_markdown(
        "```json\n{}\n```".format(
            json.dumps(builder, cls=BuilderEncoder, indent=indent)), raw=True)


def with_dbenv(func):
    def wrapper(*args, **kwargs):
        load_profile()
        return func(*args, **kwargs)
    return wrapper


@with_dbenv
def get_data_plugin(name):
    from aiida.plugins import DataFactory
    return DataFactory(name)


@with_dbenv
def load_node(identifier=None, pk=None, uuid=None, **kwargs):
    from aiida.orm import load_node
    return load_node(identifier=identifier, pk=pk, uuid=uuid, **kwargs)


def get_calc_log(calcnode):
    """get a formatted string of the calculation log"""
    from aiida.backends import get_log_messages

    def json_default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return None

    log_string = (
        "- Calc State:\n{0}\n"
        "- Scheduler Out:\n{1}\n"
        "- Scheduler Err:\n{2}\n"
        "- Log:\n{3}".format(
            calcnode.get_state(), calcnode.get_scheduler_output(),
            calcnode.get_scheduler_error(),
            json.dumps(
                get_log_messages(calcnode), default=json_default, indent=2)))
    return log_string


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
