"""
initialise a text database and profile
"""
import os
import shutil
import tempfile

from aiida.manage.fixtures import fixture_manager
import pytest

from aiida_crystal17.tests.utils import AiidaTestApp
from aiida_crystal17.tests import TEST_FILES


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

    if os.environ.get("MOCK_CRY17_EXECUTABLES", True):
        print("NB: using mock executable")
        executables = {
            'crystal17.basic': 'mock_runcry17',
            'crystal17.main': 'mock_runcry17',
            'gulp.single': 'mock_gulp',
            'gulp.optimize': 'mock_gulp'
        }
    else:
        executables = {
            'crystal17.basic': 'runcry17',
            'crystal17.main': 'runcry17',
            'gulp.single': 'gulp',
            'gulp.optimize': 'gulp'
        }

    work_directory = tempfile.mkdtemp()
    yield AiidaTestApp(
        work_directory, executables, environment=aiida_environment)
    aiida_environment.reset_db()
    shutil.rmtree(work_directory)


@pytest.fixture(scope='function')
def get_structure():
    def _get_structure(name):
        from aiida.plugins import DataFactory
        from ase.spacegroup import crystal
        from aiida_crystal17.symmetry import convert_structure
        structure_data_cls = DataFactory('structure')
        if name == "MgO":
            atoms = crystal(
                symbols=[12, 8],
                basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
                spacegroup=225,
                cellpar=[4.21, 4.21, 4.21, 90, 90, 90])
            return structure_data_cls(ase=atoms)
        elif name == "NiO_afm":
            atoms = crystal(
                symbols=[28, 8],
                basis=[[0, 0, 0], [0.5, 0.5, 0.5]],
                spacegroup=225,
                cellpar=[4.164, 4.164, 4.164, 90, 90, 90])
            atoms.set_tags([1, 1, 2, 2, 0, 0, 0, 0])
            return structure_data_cls(ase=atoms)
        elif name == "pyrite":
            structure_data = {
                "lattice": [[5.38, 0.000000, 0.000000],
                            [0.000000, 5.38, 0.000000],
                            [0.000000, 0.000000, 5.38]],
                "fcoords": [[0.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.5],
                            [0.5, 0.5, 0.0], [0.338, 0.338, 0.338],
                            [0.662, 0.662, 0.662], [0.162, 0.662, 0.838],
                            [0.838, 0.338, 0.162], [0.662, 0.838, 0.162],
                            [0.338, 0.162, 0.838], [0.838, 0.162, 0.662],
                            [0.162, 0.838, 0.338]],
                "symbols": ['Fe'] * 4 + ['S'] * 8,
                "pbc": [True, True, True]
            }
            return convert_structure(structure_data, "aiida")
        elif name == "zincblende":
            structure_data = {
                'pbc': [True, True, True],
                'atomic_numbers': [26, 26, 26, 26, 16, 16, 16, 16],
                'ccoords': [[0.0, 0.0, 0.0],
                            [2.71, 2.71, 0.0],
                            [0.0, 2.71, 2.71],
                            [2.71, 0.0, 2.71],
                            [1.355, 1.355, 1.355],
                            [4.065, 4.065, 1.355],
                            [1.355, 4.065, 4.065],
                            [4.065, 1.355, 4.065]],
                'lattice': [[5.42, 0.0, 0.0],
                            [0.0, 5.42, 0.0],
                            [0.0, 0.0, 5.42]],
                'equivalent': [0, 0, 0, 0, 0, 0, 0, 0]}
            return convert_structure(structure_data, "aiida")
        raise ValueError(name)
    return _get_structure


@pytest.fixture(scope='function')
def get_cif():
    def _get_cif(name):
        from aiida.plugins import DataFactory
        cif_data_cls = DataFactory('cif')
        if name == "pyrite":
            return cif_data_cls(file=os.path.join(TEST_FILES, "cif", "pyrite.cif"))
        raise ValueError(name)
    return _get_cif
