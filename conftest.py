"""pytest plugin configuration.

For more information on writing pytest plugins see:

- https://docs.pytest.org/en/latest/writing_plugins.html
- https://docs.pytest.org/en/latest/reference.html#request
- https://docs.pytest.org/en/latest/example/simple.html
- https://github.com/pytest-dev/cookiecutter-pytest-plugin

"""
import copy
import difflib
import os
import re
import shutil
import tempfile

from _pytest.config import Config  # noqa: F401
from _pytest.config.argparsing import Parser  # noqa: F401
from _pytest.nodes import Item  # noqa: F401
import pytest
import ruamel.yaml as yaml

from aiida.manage.fixtures import fixture_manager

from aiida_crystal17.tests import (get_test_structure, get_test_structure_and_symm, open_resource_binary,
                                   resource_context)
from aiida_crystal17.tests.utils import AiidaTestApp

CRY17_CALL_EXEC_MARKER = 'cry17_calls_executable'
CRY17_NOTEBOOK_MARKER = 'cry17_doc_notebooks'

CRY17_NO_MOCK_HELP = 'Do not use mock executables for tests.'
CRY17_WORKDIR_HELP = ('Specify a work directory path for aiida calcjob execution. '
                      'If not specified, a temporary directory is used and deleted after tests execution.')
CRY17_SKIP_EXEC_HELP = ('skip tests marked with @pytest.mark.{}'.format(CRY17_CALL_EXEC_MARKER))
CRY17_NB_TEST_HELP = ('Only run tests marked {} (otherwise skipped)'.format(CRY17_NOTEBOOK_MARKER))
CRY17_NB_REGEN_HELP = (
    'Only run tests marked {} (otherwise skipped) and regenrerate files'.format(CRY17_NOTEBOOK_MARKER))


def pytest_addoption(parser):
    # type: (Parser) -> None
    """Define pytest command-line and configuration file options.

    Configuration file options are set in pytest.ini|tox.ini|setup.cfg as e.g.::

        [pytest]
        cry17_no_mock = false

    Configuration options can be accessed via the `pytestconfig` fixture::

        @pytest.fixture
        def my_fixture(pytestconfig)
            pytestconfig.getoption('cry17_no_mock')
            pytestconfig.getini('cry17_no_mock')

    """
    group = parser.getgroup('aiida_crystal17')
    group.addoption('--cry17-no-mock',
                    action='store_true',
                    dest='cry17_no_mock',
                    default=False,
                    help=CRY17_NO_MOCK_HELP)
    group.addoption('--cry17-workdir', dest='cry17_workdir', default=None, help=CRY17_WORKDIR_HELP)
    group.addoption('--cry17-skip-exec',
                    action='store_true',
                    dest='cry17_skip_exec',
                    default=False,
                    help=CRY17_SKIP_EXEC_HELP)
    group.addoption('--cry17-nbs-test',
                    action='store_true',
                    dest='cry17_nbs_test',
                    default=False,
                    help=CRY17_NB_TEST_HELP)
    group.addoption('--cry17-nbs-regen',
                    action='store_true',
                    dest='cry17_nbs_regen',
                    default=False,
                    help=CRY17_NB_REGEN_HELP)

    parser.addini('cry17_no_mock', CRY17_NO_MOCK_HELP, type='bool', default=False)
    parser.addini('cry17_workdir', CRY17_WORKDIR_HELP, default=None)


def use_mock_exec(config):
    """Return whether mock executables should be used."""
    if config.getoption('cry17_no_mock') or config.getini('cry17_no_mock'):
        return False
    return True


def get_work_directory(config):
    """Return the aiida work directory to use."""
    if config.getoption('cry17_workdir') is not None:
        return config.getoption('cry17_workdir')
    if config.getini('cry17_workdir') is not None:
        return config.getini('cry17_workdir')
    return None


def run_notebook_tests(config):
    """Return whether notebook tests should be run."""
    return config.getoption('cry17_nbs_test', False) or config.getoption('cry17_nbs_regen', False)


def pytest_configure(config):
    # type: (Config) -> None
    """Register pytest markers.

    These will show in ``pytest --markers``
    """
    config.addinivalue_line('markers',
                            '{}: mark tests that will call external executables'.format(CRY17_CALL_EXEC_MARKER))
    config.addinivalue_line('markers', '{}: mark tests that will test document notebooks'.format(CRY17_NOTEBOOK_MARKER))


def pytest_collection_modifyitems(config, items):
    # type: (Config, list) -> None
    """Add skip marker to tests based on markers.

    - if ``cry17_calls_executable`` and ``cry17_skip_exec = True``
    - if ``cry17_calls_executable(skip_non_mock=True)`` and not running with mock executables.

    - if not ``cry17_test_nbs``, skip tests with ``cry17_doc_notebooks`` marker
    - if ``cry17_test_nbs``, only run tests with ``cry17_doc_notebooks`` marker

    """
    for item in items:  # type: Item

        if run_notebook_tests(config):
            if CRY17_NOTEBOOK_MARKER not in item.keywords:
                item.add_marker(pytest.mark.skip(reason='Running tests marked {} only'.format(CRY17_NOTEBOOK_MARKER)))
                continue
        elif CRY17_NOTEBOOK_MARKER in item.keywords:
            item.add_marker(pytest.mark.skip(reason='Not running tests marked {}'.format(CRY17_NOTEBOOK_MARKER)))
            continue

        if CRY17_CALL_EXEC_MARKER not in item.keywords:
            continue
        marker = item.get_closest_marker(CRY17_CALL_EXEC_MARKER)

        if config.getoption('cry17_skip_exec', False):
            item.add_marker(pytest.mark.skip(reason='cry17_skip_exec specified'))
        elif marker.kwargs.get('skip_non_mock', False) and not use_mock_exec(config):
            item.add_marker(
                pytest.mark.skip(reason='running with mock executables and skip_non_mock specified: {}'.format(
                    marker.kwargs.get('reason', ''))))


@pytest.fixture(scope='session')
def aiida_environment():
    """Set up an aiida database, profile and for the duration of the tests."""
    # TODO this is required locally for click
    # (see https://click.palletsprojects.com/en/7.x/python3/)
    os.environ['LC_ALL'] = 'en_US.UTF-8'
    with fixture_manager() as fixture_mgr:
        yield fixture_mgr


@pytest.fixture(scope='function')
def db_test_app(aiida_environment, pytestconfig):
    """Create a clean aiida database, profile and temporary work directory for the duration of a test.

    :rtype: aiida_crystal17.tests.utils.AiidaTestApp

    """
    if use_mock_exec(pytestconfig):
        print('NB: using mock executable')
        executables = {
            'crystal17.basic': 'mock_crystal17',
            'crystal17.main': 'mock_crystal17',
            'crystal17.doss': 'mock_properties17',
            'crystal17.fermi': 'mock_properties17',
            'gulp.single': 'mock_gulp',
            'gulp.optimize': 'mock_gulp',
            'gulp.fitting': 'mock_gulp'
        }
    else:
        executables = {
            'crystal17.basic': 'crystal17',
            'crystal17.main': 'crystal17',
            'crystal17.doss': 'properties17',
            'crystal17.fermi': 'properties17',
            'gulp.single': 'gulp',
            'gulp.optimize': 'gulp',
            'gulp.fitting': 'gulp'
        }

    test_workdir = get_work_directory(pytestconfig)
    if test_workdir:
        print('NB: using test workdir: {}'.format(test_workdir))
        work_directory = test_workdir
    else:
        work_directory = tempfile.mkdtemp()
    yield AiidaTestApp(work_directory, executables, environment=aiida_environment)
    aiida_environment.reset_db()
    if not test_workdir:
        shutil.rmtree(work_directory)


def nb_to_dict(nb, strip_keys=()):
    """Recursively convert dict-like NotebookNode to dict."""
    from nbformat import NotebookNode
    if isinstance(nb, (NotebookNode, dict)):
        return {k: nb_to_dict(nb[k], strip_keys) for k in sorted(nb.keys()) if k not in strip_keys}
    elif isinstance(nb, (tuple, list)):
        return [nb_to_dict(i, strip_keys) for i in nb]
    else:
        return nb


def nb_to_yaml_str(nb, strip_keys=(), default_flow_style=False):
    """Convert a `NotebookNode`, dict or list, to a formatted yaml string."""
    nb_dict = nb_to_dict(nb, strip_keys=strip_keys)
    # converts all strings that have a newline in them to block style strings
    format_map = yaml.compat.ordereddict()
    format_map['\n'] = yaml.scalarstring.preserve_literal
    format_map['\\e'] = yaml.scalarstring.FoldedScalarString
    yaml.scalarstring.walk_tree(nb_dict, map=format_map)
    # use default_flow_style, so dict keys are on separate lines
    return '\n{}'.format(yaml.round_trip_dump(nb_dict, default_flow_style=default_flow_style))


def compare_text(obtained, expected, rstrip=True):
    """Compare two pieces of text.

    :param str obtained: obtained text.
    :param str expected: expected text.

    """
    obtained_lines = [l.rstrip() if rstrip else l for l in obtained.splitlines()]
    expected_lines = [l.rstrip() if rstrip else l for l in expected.splitlines()]

    if obtained_lines != expected_lines:
        diff_lines = list(difflib.unified_diff(expected_lines, obtained_lines, lineterm=''))
        if len(diff_lines) <= 500:
            return '\n'.join(diff_lines)
        else:
            return 'Texts are different, but diff is too big to show ({} lines)'.format(len(diff_lines))
    return None


RGX_CARRIAGERETURN = re.compile(r'.*\r(?=[^\n])')
RGX_BACKSPACE = re.compile(r'[^\n]\b')


def coalesce_streams(outputs):
    """Merge all stream outputs with shared names into single streams, to ensure deterministic outputs.

    Adapted from https://github.com/computationalmodelling/nbval/blob/master/nbval/plugin.py

    Parameters
    ----------
    outputs : list
        Outputs being processed

    """
    if not outputs:
        return outputs

    new_outputs = []
    streams = {}
    for output in outputs:
        if (output.output_type == 'stream'):
            if output.name in streams:
                streams[output.name].text += output.text
            else:
                new_outputs.append(output)
                streams[output.name] = output
        else:
            new_outputs.append(output)

    # process \r and \b characters
    for output in streams.values():
        old = output.text
        while len(output.text) < len(old):
            old = output.text
            # Cancel out anything-but-newline followed by backspace
            output.text = RGX_BACKSPACE.sub('', output.text)
        # Replace all carriage returns not followed by newline
        output.text = RGX_CARRIAGERETURN.sub('', output.text)

    return new_outputs


def compare_nb_outputs(obtained,
                       expected,
                       strip_keys=('prompt_number', 'execution_count', 'traceback',
                                   'application/vnd.jupyter.widget-view+json', 'image/svg+xml', 'image/png',
                                   'image/jpeg', 'image/jpg')):
    """Compare two section of a Jupyter Notebook."""
    return compare_text(nb_to_yaml_str(obtained, strip_keys=strip_keys), nb_to_yaml_str(expected,
                                                                                        strip_keys=strip_keys))


@pytest.fixture(scope='function')
def nb_regression():
    """Fixture used to execute a Jupyter Notebook, and test its output is as expected.

    Use::

        new_notebook = nb_regression.check(handle, as_version=4, execute=True, timeout=120, cwd=None)

    :param handle: a file handle to read the notebook from.
    :param as_version: The version of the notebook format to return.
    :param execute: Whether to execute the notebook
    :param allow_errors: If False, execution is stopped after the first unexpected exception
                         (not tagged ``raises-exception``).
    :param timeout: The maximum time to wait (in seconds) for execution of each cell.
    :param cwd: Path to the directory which the notebook will run in (default is temporary directory).

    By default, an error will be recorded if at least one Notebook code cells outputs an exception.

    Additionally, Notebook code cells can be tagged (see https://github.com/jupyter/notebook/pull/2048) with:

    - ``nbreg_compare_output`` assert all outputs of the code cell are exactly equal to those in the input notebook
      (ignoring non-deterministic fields, such as ``execution_count`` and ``traceback``)
    - ``raises-exception`` check that the output of the cell includes an exception

    """
    from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
    import nbformat
    from nbformat import NotebookNode

    # also requires jupyter_client

    # Note: Could use https://github.com/computationalmodelling/nbval,
    # but this treats the whole notebook file as the test file, so doesn't allow
    # programmatic access to the file before/after testing.

    class NB_Regression(object):

        def __init__(self, regen_notebook=False):
            self.regen_notebook = regen_notebook

        def check(self,
                  handle,
                  as_version=4,
                  execute=True,
                  allow_errors=False,
                  timeout=120,
                  cwd=None,
                  compare_all=False,
                  max_source_lines=10):
            notebook = nbformat.read(handle, as_version=as_version)  # type: NotebookNode
            proc = ExecutePreprocessor(timeout=timeout, allow_errors=allow_errors)
            new_notebook = copy.deepcopy(notebook)
            errors = {}
            if execute:
                if not cwd:
                    cwd_dir = tempfile.mkdtemp()
                resources = {
                    'metadata': {
                        'path': cwd or cwd_dir
                    }
                }  # metadata/path specifies the directory the kernel will run in
                try:
                    proc.preprocess(new_notebook, resources)
                except CellExecutionError:
                    errors['Notebook'] = 'Halted execution after CellExecutionError raised'
                finally:
                    if not cwd:
                        shutil.rmtree(cwd_dir)

            if self.regen_notebook:
                handle.seek(0)
                nbformat.write(new_notebook, handle)

            for i, cell in enumerate(new_notebook.cells):
                key = 'Cell_{}'.format(i + 1)

                # for an errored cell, show maximum of 10 lines of source code
                source_lines = cell.source.splitlines()
                if len(source_lines) <= max_source_lines:
                    default = {'_source': cell.source}
                else:
                    default = {'_source': '\n'.join(cell.source.splitlines()[:max_source_lines]) + '\n...'}

                if 'outputs' in cell and ('nbreg_compare_output' in cell.metadata.get('tags', []) or compare_all):
                    # directly compare the outputs
                    diff = compare_nb_outputs(coalesce_streams(cell.outputs),
                                              coalesce_streams(notebook.cells[i].outputs))
                    if diff:
                        errors.setdefault(key, default)['comparison'] = diff
                    continue

                exception_found = False
                if 'outputs' in cell:
                    # check the output does not contain any exceptions
                    for output in cell['outputs']:
                        if output.output_type == 'error':
                            if 'raises-exception' in cell.metadata.get('tags', []):
                                exception_found = True
                            else:
                                errors.setdefault(key, default)['exception'] = output

                if 'raises-exception' in cell.metadata.get('tags', []) and not exception_found:
                    errors.setdefault(key, default)['no_exception'] = True

            if errors:
                errors_str = nb_to_yaml_str(errors)
                raise AssertionError(errors_str)

            return new_notebook

    return NB_Regression()


@pytest.fixture(scope='function')
def get_structure():
    """Return a function that returns a test `aiida.orm.StructureData` instance."""
    return get_test_structure


@pytest.fixture(scope='function')
def get_structure_and_symm():
    """Return a function that returns test `aiida.orm.StructureData` and `SymmetryData` instances."""
    return get_test_structure_and_symm


@pytest.fixture(scope='function')
def get_cif():
    """Return a function that returns a test `aiida.orm.CifData` instance."""

    def _get_cif(name):
        from aiida.orm import CifData
        if name == 'pyrite':
            with open_resource_binary('cif', 'pyrite.cif') as handle:
                return CifData(file=handle)
        raise ValueError(name)

    return _get_cif


@pytest.fixture(scope='function')
def upload_basis_set_family():
    """Upload a basis set family."""
    from aiida_crystal17.data.basis_set import BasisSetData

    def _upload(folder_name='sto3g', group_name='sto3g', stop_if_existing=True):
        with resource_context('basis_sets', folder_name) as path:
            BasisSetData.upload_basisset_family(path,
                                                group_name,
                                                'minimal basis sets',
                                                stop_if_existing=stop_if_existing,
                                                extension='.basis')
        return BasisSetData.get_basis_group_map(group_name)

    return _upload
