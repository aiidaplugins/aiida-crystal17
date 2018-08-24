"""
initialise a text database and profile
"""
from aiida.utils.fixtures import fixture_manager
import pytest


@pytest.fixture(scope='session')
def aiida_profile():
    with fixture_manager() as fixture_mgr:
        yield fixture_mgr
