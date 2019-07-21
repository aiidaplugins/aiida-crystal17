"""Validate consistency of versions and dependencies.

Validates consistency of setup.json and

 * environment.yml
 * version in aiida/__init__.py
"""
from collections import OrderedDict
import json
import os
import sys

import click

FILENAME_SETUP_JSON = 'setup.json'
SCRIPT_PATH = os.path.split(os.path.realpath(__file__))[0]
ROOT_DIR = os.path.join(SCRIPT_PATH, os.pardir)
FILEPATH_SETUP_JSON = os.path.join(ROOT_DIR, FILENAME_SETUP_JSON)


def get_setup_json():
    """Return the `setup.json` as a python dictionary """
    with open(FILEPATH_SETUP_JSON, 'r') as fil:
        setup_json = json.load(fil, object_pairs_hook=OrderedDict)

    return setup_json


@click.group()
def cli():
    pass


@cli.command('version')
def validate_version():
    """Check that version numbers match.

    Check version number in setup.json and aiida_crystal17/__init__.py and make sure
    they match.
    """
    # Get version from python package
    sys.path.insert(0, ROOT_DIR)
    import aiida_crystal17  # pylint: disable=wrong-import-position
    version = aiida_crystal17.__version__

    setup_content = get_setup_json()
    if version != setup_content['version']:
        click.echo("Version number mismatch detected:")
        click.echo("Version number in '{}': {}".format(FILENAME_SETUP_JSON, setup_content['version']))
        click.echo("Version number in '{}/__init__.py': {}".format('aiida_crystal17', version))
        click.echo("Updating version in '{}' to: {}".format(FILENAME_SETUP_JSON, version))

        setup_content['version'] = version
        with open(FILEPATH_SETUP_JSON, 'w') as fil:
            # Write with indentation of two spaces and explicitly define separators to not have spaces at end of lines
            json.dump(setup_content, fil, indent=2, separators=(',', ': '))

        sys.exit(1)


@cli.command('conda')
def update_environment_yml():
    """
    Updates environment.yml file for conda.
    """
    import yaml
    import re

    # needed for ordered dict, see
    # https://stackoverflow.com/a/52621703
    yaml.add_representer(
        OrderedDict,
        lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()),
        Dumper=yaml.SafeDumper)

    # fix incompatibilities between conda and pypi
    replacements = {}
    install_requires = get_setup_json()['install_requires']

    conda_requires = []
    for req in install_requires:
        # skip packages required for specific python versions
        # (environment.yml aims at the latest python version)
        if req.find("python_version") != -1:
            continue

        for (regex, replacement) in iter(replacements.items()):
            req = re.sub(regex, replacement, req)

        conda_requires.append(req)

    environment = OrderedDict([
        ('name', 'aiida_crystal17'),
        ('channels', ['conda-forge']),
        ('dependencies', conda_requires),
    ])

    environment_filename = 'environment.yml'
    file_path = os.path.join(ROOT_DIR, environment_filename)
    with open(file_path, 'w') as env_file:
        env_file.write('# Usage: conda env create -n myenvname -f environment.yml python=3.6\n')
        yaml.safe_dump(
            environment, env_file, explicit_start=True, default_flow_style=False, encoding='utf-8', allow_unicode=True)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
