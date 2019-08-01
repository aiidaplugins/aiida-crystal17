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
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo
from aiida.common import EntryPointError
from aiida.plugins.entry_point import get_entry_point_names, load_entry_point


@verdi.group('gulp.potentials')
def potentials():
    """interface for working with GULP potentials"""


@potentials.command('list')
@click.argument('entry_point', type=click.STRING, required=False)
@click.option('-d', '--depth', 'schema_depth', default=2, help='nested depth with which to print data schema')
def potential_list(entry_point, schema_depth):
    """Display a list of all available plugins"""
    entry_point_group = 'gulp.potentials'
    if entry_point:
        try:
            plugin = load_entry_point(entry_point_group, entry_point)
        except EntryPointError as exception:
            echo.echo_critical(str(exception))
        else:
            try:
                echo.echo(str(plugin.get_description()), bold=True)
            except (AttributeError, TypeError):
                echo.echo_error('No description available for {}'.format(entry_point))
            try:
                schema = plugin.get_schema()
                echo.echo('Data Schema:')
                edict.pprint(schema, depth=schema_depth, print_func=echo.echo, keycolor='blue')
            except (AttributeError, TypeError):
                echo.echo_error('No validation schema available for {}'.format(entry_point))
    else:
        entry_points = get_entry_point_names(entry_point_group)
        if entry_points:
            echo.echo('Registered entry points for {}:'.format(entry_point_group))
            for registered_entry_point in entry_points:
                echo.echo('* {}'.format(registered_entry_point))

            echo.echo('')
            echo.echo_info('Pass the entry point as an argument to display detailed information')
        else:
            echo.echo_error('No plugins found for group {}'.format(entry_point_group))
