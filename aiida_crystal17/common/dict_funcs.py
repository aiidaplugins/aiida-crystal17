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
from collections import Mapping
import json
from textwrap import wrap
from jsonextended import edict


def unflatten_dict(indict, delimiter='.'):
    return edict.unflatten(indict, key_as_tuple=False, delim=delimiter)


def flatten_dict(indict, delimiter='.'):
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
                raise ValueError('could not find key path: {}'.format(keys[0:i + 1]))
            else:
                return default
    return subdct


def map_nested_dicts(ob, func, apply_lists=False):
    """ map a function on to all values of a nested dictionary """
    if isinstance(ob, Mapping):
        return {k: map_nested_dicts(v, func, apply_lists) for k, v in ob.items()}
    elif apply_lists and isinstance(ob, (list, tuple)):
        return [map_nested_dicts(v, func, apply_lists) for v in ob]
    else:
        return func(ob)


def recursive_round(dct, dp):
    """ recursively apply the `round` function to all floats in a dict"""

    def _round(value):
        if isinstance(value, float):
            value = round(value, dp)
        return value

    return map_nested_dicts(dct, _round, True)


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
    return display_markdown('```json\n{}\n```'.format(json.dumps(builder, cls=BuilderEncoder, indent=indent)), raw=True)
