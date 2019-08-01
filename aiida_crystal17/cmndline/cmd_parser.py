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
import io

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida_crystal17.cmndline import options


@verdi.group('crystal17.parse')
def parse():
    """Commandline interface for parsing crystal files to JSON/YAML."""


@parse.command()
@arguments.INPUT_FILE()
@options.DICT_KEYS()
@options.DICT_FORMAT()
def stdin(input_file, keys, fmt):
    """Parse an existing stdin (d12) file, created from a crystal run."""
    from aiida_crystal17.parsers.raw.inputd12_read import extract_data
    with io.open(input_file) as handle:
        data, bases, atom_props = extract_data(handle.read())
    if keys is not None:
        data = {k: v for k, v in data.items() if k in keys}
    options.echo_dictionary(data, fmt=fmt)


@parse.command()
@arguments.INPUT_FILE()
@options.DICT_KEYS()
@options.DICT_FORMAT()
def stdout(input_file, keys, fmt):
    """Parse an existing stdout file, created from a crystal run."""
    from aiida_crystal17.parsers.raw.crystal_stdout import read_crystal_stdout
    with io.open(input_file) as handle:
        data = read_crystal_stdout(handle.read())
    if keys is not None:
        data = {k: v for k, v in data.items() if k in keys}
    options.echo_dictionary(data, fmt=fmt)


@parse.command('doss-f25')
@arguments.INPUT_FILE()
@options.DICT_KEYS()
@options.DICT_FORMAT()
def doss_f25(input_file, keys, fmt):
    """Parse an existing fort.25 file, created from a crystal properties DOSS calculation."""
    from aiida_crystal17.parsers.raw.crystal_fort25 import parse_crystal_fort25
    with io.open(input_file) as handle:
        data = parse_crystal_fort25(handle.read())
    if keys is not None:
        data = {k: v for k, v in data.items() if k in keys}
    options.echo_dictionary(data, fmt=fmt)
