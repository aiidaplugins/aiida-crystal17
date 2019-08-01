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
import click
from jsonextended import edict
from aiida.orm import load_node
from aiida.plugins import DataFactory
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators


@verdi.group('crystal17.symmetry')
def symmetry():
    """Commandline interface for working with SymmetryData"""


@symmetry.command()
@click.option('--symmetries', '-s', is_flag=True, help='show full symmetry operations')
@click.argument('pk', type=int)
@decorators.with_dbenv()
def show(pk, symmetries):
    """show the contents of a symmetryData"""
    node = load_node(pk)

    if not isinstance(node, DataFactory('crystal17.symmetry')):
        click.echo("The node was not of type 'crystal17.symmetry'", err=True)
    elif symmetries:
        edict.pprint(node.data, print_func=click.echo, round_floats=5)
    else:
        edict.pprint(node.attributes, print_func=click.echo)


@symmetry.command()
def schema():
    """view the validation schema"""
    schema = DataFactory('crystal17.symmetry').data_schema
    edict.pprint(schema, depth=None, print_func=click.echo)
