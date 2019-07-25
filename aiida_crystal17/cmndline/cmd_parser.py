import io

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import echo


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
    echo.echo_dictionary(data, fmt=fmt)


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
    echo.echo_dictionary(data, fmt=fmt)
