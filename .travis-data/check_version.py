"""Validate consistency of versions and dependencies.

Validates consistency of setup.json and

 * environment.yml
 * version in aiida/__init__.py
"""
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
    with open(FILEPATH_SETUP_JSON, 'r') as handle:
        setup_json = json.load(handle)  # , object_pairs_hook=OrderedDict)

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
        click.echo('Version number mismatch detected:')
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
    Updates conda_dev_env.yml file for conda.
    """
    import re
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
    from ruamel.yaml import YAML

    environment_filename = 'conda_dev_env.yml'

    cmap = CommentedMap()
    cmap.yaml_set_start_comment(('Usage: conda env create -n myenvname -f {} python=3.6\n'
                                 '       conda activate myenvname\n'
                                 '       pip install --no-deps -e .'.format(environment_filename)))
    cmap['name'] = 'aiida_crystal17'
    cmap['channels'] = CommentedSeq(['conda-forge', 'cjs14'])
    cmap['channels'].yaml_add_eol_comment('for sqlalchemy-diff and pgtest', 1)
    cmap['dependencies'] = dmap = CommentedSeq()

    # additional packages
    dmap.append('pip')
    dmap.append('aiida-core.services')

    # fix incompatibilities between conda and pypi
    replacements = {'pre-commit': 'pre_commit'}
    setup_json = get_setup_json()

    for base, key in [(None, 'install_requires'), ('extras_require', 'testing'), ('extras_require', 'code_style'),
                      ('extras_require', 'docs')]:
        requirements = setup_json.get(base, setup_json)[key]
        count = 0
        for req in sorted(requirements, key=lambda x: x.lower()):
            # skip packages required for specific python versions < 3
            if re.findall("python_version\\s*\\<\\s*\\'?3", req):
                continue
            req = req.split(';')[0]
            for (regex, replacement) in iter(replacements.items()):
                req = re.sub(regex, replacement, req)
            count += 1
            dmap.append(req.lower())

        dmap.yaml_set_comment_before_after_key(len(dmap) - count, before=key)

    yaml = YAML(typ='rt')
    yaml.default_flow_style = False
    yaml.encoding = 'utf-8'
    yaml.allow_unicode = True
    file_path = os.path.join(ROOT_DIR, environment_filename)
    with open(file_path, 'w') as env_file:
        yaml.dump(cmap, env_file)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
