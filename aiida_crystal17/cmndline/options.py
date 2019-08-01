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
"""Common click options for verdi commands"""
from collections import OrderedDict
import json
import yaml

import click
from aiida.cmdline.params.options.overridable import OverridableOption
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.params.options import FORCE, DESCRIPTION  # noqa: F401
from aiida.cmdline.utils.echo import echo

FAMILY_NAME = OverridableOption('--name', required=True, help='Name of the BasisSet family')
PATH = OverridableOption('--path', default='.', type=click.Path(exists=True), help='Path to the folder')

DRY_RUN = OverridableOption(
    '--dry-run', is_flag=True, is_eager=True, help='do not commit to database or modify configuration files')

# TODO DICT_FORMAT, DICT_KEYS are part of aiida-core post v1.0.0b5

VALID_DICT_FORMATS_MAPPING = OrderedDict((('yaml', yaml.dump), ('json',
                                                                lambda d: json.dumps(d, indent=2, sort_keys=True)),
                                          ('yaml_expanded', lambda d: yaml.dump(d, default_flow_style=False))))

DICT_FORMAT = OverridableOption(
    '-f',
    '--format',
    'fmt',
    type=click.Choice(list(VALID_DICT_FORMATS_MAPPING.keys())),
    default=list(VALID_DICT_FORMATS_MAPPING.keys())[0],
    help='The format of the output data.')


def echo_dictionary(dictionary, fmt):
    """
    Print the given dictionary to stdout in the given format

    :param dictionary: the dictionary
    :param fmt: the format to use for printing
    """
    try:
        format_function = VALID_DICT_FORMATS_MAPPING[fmt]
    except KeyError:
        formats = ', '.join(VALID_DICT_FORMATS_MAPPING.keys())
        raise ValueError('Unrecognised printing format. Valid formats are: {}'.format(formats))

    echo(format_function(dictionary))


DICT_KEYS = OverridableOption(
    '-k', '--keys', type=click.STRING, cls=MultipleValueOption, help='Filter the output by one or more keys.')
