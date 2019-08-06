"""pytest plugin configuration.

For more information on writing pytest plugins see:

- https://docs.pytest.org/en/latest/writing_plugins.html
- https://docs.pytest.org/en/latest/reference.html#request
- https://docs.pytest.org/en/latest/example/simple.html
- https://github.com/pytest-dev/cookiecutter-pytest-plugin

"""
import os
import shutil
import tempfile

from _pytest.config import Config  # noqa: F401
from _pytest.config.argparsing import Parser  # noqa: F401
from _pytest.nodes import Item  # noqa: F401
import pytest

from aiida.manage.fixtures import fixture_manager

from aiida_crystal17.tests import (get_test_structure, get_test_structure_and_symm, open_resource_binary,
                                   resource_context)
from aiida_crystal17.tests.utils import AiidaTestApp

CRY17_CALL_EXEC_MARKER = 'cry17_calls_executable'
CRY17_NO_MOCK_HELP = 'Do not use mock executables for tests.'
CRY17_WORKDIR_HELP = ('Specify a work directory path for aiida calcjob execution. '
                      'If not specified, a temporary directory is used and deleted after tests execution.')
CRY17_SKIP_EXEC_HELP = ('skip tests marked with: @pytest.mark.{}'.format(CRY17_CALL_EXEC_MARKER))


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


def pytest_configure(config):
    # type: (Config) -> None
    """Register pytest markers.

    These will show in ``pytest --markers``
    """
    config.addinivalue_line('markers',
                            '{}: mark tests that will call external executables'.format(CRY17_CALL_EXEC_MARKER))


def pytest_collection_modifyitems(config, items):
    # type: (Config, list) -> None
    """Add skip marker to tests based on markers.

    - if ``cry17_calls_executable`` and ``cry17_skip_exec = True``
    - if ``cry17_calls_executable(skip_non_mock=True)`` and not running with mock executables.

    """
    for item in items:  # type: Item
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
