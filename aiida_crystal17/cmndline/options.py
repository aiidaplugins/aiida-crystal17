"""Common click options for verdi commands"""
import click

from aiida.cmdline.params.options.overridable import OverridableOption
from aiida.cmdline.params.options import FORCE, DESCRIPTION  # noqa: F401

FAMILY_NAME = OverridableOption(
    '--name', required=True, help='Name of the BasisSet family')
PATH = OverridableOption(
    '--path',
    default='.',
    type=click.Path(exists=True),
    help='Path to the folder')

DRY_RUN = OverridableOption(
    '--dry-run',
    is_flag=True,
    is_eager=True,
    help='do not commit to database or modify configuration files')
