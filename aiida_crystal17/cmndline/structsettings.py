import click
from aiida_crystal17.aiida_compatability import cmp_load_verdi_data
from aiida import load_dbenv, is_dbenv_loaded
from jsonextended import edict

VERDI_DATA = cmp_load_verdi_data()

# TODO add tests


@VERDI_DATA.group('cry17-settings')
def structsettings():
    """Commandline interface for working with StructSettingsData"""


@structsettings.command()
@click.option(
    '--symmetries', '-s', is_flag=True, help="show full symmetry operations")
@click.argument('pk', type=int)
def show(pk, symmetries):
    """show the contents of a StructSettingsData"""
    if not is_dbenv_loaded():
        load_dbenv()
    from aiida.orm import load_node
    from aiida.orm import DataFactory

    node = load_node(pk)

    if not isinstance(node, DataFactory('crystal17.structsettings')):
        click.echo(
            "The node was not of type 'crystal17.structsettings'", err=True)
    elif symmetries:
        edict.pprint(node.data, print_func=click.echo, round_floats=5)
    else:
        edict.pprint(dict(node.iterattrs()), print_func=click.echo)


@structsettings.command()
def schema():
    """view the validation schema"""
    if not is_dbenv_loaded():
        load_dbenv()
    from aiida.orm import DataFactory
    schema = DataFactory('crystal17.structsettings').data_schema
    edict.pprint(schema, depth=None, print_func=click.echo)
