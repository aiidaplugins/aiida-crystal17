from decimal import Decimal
import re


def convert_units(value, in_units, out_units, standard="codata2014"):
    # TODO use units.yaml
    if in_units == "hartree" and out_units == "eV":
        return value * 27.21138602


def split_numbers(string, as_decimal=False):
    """ get a list of numbers from a string (even with no spacing)

    :type string: str
    :type as_decimal: bool
    :param as_decimal: if True return floats as decimal.Decimal objects

    :rtype: list

    :Example:

    >>> split_numbers("1")
    [1.0]

    >>> split_numbers("1 2")
    [1.0, 2.0]

    >>> split_numbers("1.1 2.3")
    [1.1, 2.3]

    >>> split_numbers("1e-3")
    [0.001]

    >>> split_numbers("-1-2")
    [-1.0, -2.0]

    >>> split_numbers("1e-3-2")
    [0.001, -2.0]

    """
    _match_number = re.compile(
        '-?\\ *[0-9]+\\.?[0-9]*(?:[Ee]\\ *[+-]?\\ *[0-9]+)?')
    string = string.replace(" .", " 0.")
    string = string.replace("-.", "-0.")
    return [
        Decimal(s) if as_decimal else float(s)
        for s in re.findall(_match_number, string)
    ]
