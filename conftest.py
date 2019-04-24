"""
initialise a text database and profile
"""
import os
import shutil
import tempfile

from aiida.manage.fixtures import fixture_manager
import pytest

from aiida_crystal17.tests.aiida_test_app import AiidaTestApp


@pytest.fixture(scope='session')
def aiida_profile():
    """setup a test profile for the duration of the tests"""
    # TODO this is required locally for click
    # (see https://click.palletsprojects.com/en/7.x/python3/)
    os.environ["LC_ALL"] = "en_US.UTF-8"
    with fixture_manager() as fixture_mgr:
        yield fixture_mgr


@pytest.fixture(scope='function')
def db_test_app(aiida_profile):
    """clear the database after each test"""
    work_directory = tempfile.mkdtemp()

    if os.environ.get("MOCK_CRY17_EXECUTABLES", False):
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

    yield AiidaTestApp(aiida_profile, work_directory, executables)
    aiida_profile.reset_db()
    shutil.rmtree(work_directory)
