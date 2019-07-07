"""
initialise a text database and profile
"""
import os
import shutil
import tempfile

from aiida.manage.fixtures import fixture_manager
import pytest

from aiida_crystal17.tests.utils import AiidaTestApp
from aiida_crystal17.tests import TEST_FILES, get_test_structure


@pytest.fixture(scope='session')
def aiida_environment():
    """setup a test profile for the duration of the tests"""
    # TODO this is required locally for click
    # (see https://click.palletsprojects.com/en/7.x/python3/)
    os.environ["LC_ALL"] = "en_US.UTF-8"
    with fixture_manager() as fixture_mgr:
        yield fixture_mgr


@pytest.fixture(scope='function')
def db_test_app(aiida_environment):
    """clear the database after each test"""
    if os.environ.get("MOCK_CRY17_EXECUTABLES", True) != "false":
        print("NB: using mock executable")
        executables = {
            'crystal17.basic': 'mock_crystal17',
            'crystal17.main': 'mock_crystal17',
            'crystal17.doss': 'mock_properties17',
            'crystal17.fermi': 'mock_properties17',
            'gulp.single': 'mock_gulp',
            'gulp.optimize': 'mock_gulp'
        }
    else:
        executables = {
            'crystal17.basic': 'crystal17',
            'crystal17.main': 'crystal17',
            'crystal17.doss': 'properties17',
            'crystal17.fermi': 'properties17',
            'gulp.single': 'gulp',
            'gulp.optimize': 'gulp'
        }

    # work_directory = tempfile.mkdtemp()
    work_directory = "test_workdir"
    yield AiidaTestApp(
        work_directory, executables, environment=aiida_environment)
    aiida_environment.reset_db()
    # shutil.rmtree(work_directory)


@pytest.fixture(scope='function')
def get_structure():
    return get_test_structure


@pytest.fixture(scope='function')
def get_cif():
    def _get_cif(name):
        from aiida.plugins import DataFactory
        cif_data_cls = DataFactory('cif')
        if name == "pyrite":
            return cif_data_cls(file=os.path.join(TEST_FILES, "cif", "pyrite.cif"))
        raise ValueError(name)
    return _get_cif


@pytest.fixture(scope='function')
def upload_basis_set_family():
    """ upload the a basis set family"""
    from aiida_crystal17.data.basis_set import BasisSetData

    def _upload(name="sto3g"):
        return BasisSetData.upload_basisset_family(
            os.path.join(TEST_FILES, "basis_sets", name),
            name,
            "minimal basis sets",
            stop_if_existing=True,
            extension=".basis")
    return _upload
