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
from aiida.manage.tests import test_manager
import pytest

from aiida_crystal17.tests import (
    get_test_structure,
    get_test_structure_and_symm,
    open_resource_binary,
    resource_context,
)
from aiida_crystal17.tests.utils import AiidaTestApp

pytest_plugins = ['aiida.manage.tests.pytest_fixtures'] 


CRY17_CALL_EXEC_MARKER = "cry17_calls_executable"
CRY17_NOTEBOOK_MARKER = "cry17_doc_notebooks"

CRY17_NO_MOCK_HELP = "Do not use mock executables for tests."
CRY17_WORKDIR_HELP = (
    "Specify a work directory path for aiida calcjob execution. "
    "If not specified, a temporary directory is used and deleted after tests execution."
)
CRY17_SKIP_EXEC_HELP = "skip tests marked with @pytest.mark.{}".format(
    CRY17_CALL_EXEC_MARKER
)
CRY17_NB_TEST_HELP = "Only run tests marked {} (otherwise skipped)".format(
    CRY17_NOTEBOOK_MARKER
)


class NotSet(object):
    """Indicate that a configuration file variable was not set."""


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
    group = parser.getgroup("aiida_crystal17")
    group.addoption(
        "--cry17-no-mock",
        action="store_true",
        dest="cry17_no_mock",
        default=False,
        help=CRY17_NO_MOCK_HELP,
    )
    group.addoption(
        "--cry17-workdir", dest="cry17_workdir", default=None, help=CRY17_WORKDIR_HELP
    )
    group.addoption(
        "--cry17-skip-exec",
        action="store_true",
        dest="cry17_skip_exec",
        default=False,
        help=CRY17_SKIP_EXEC_HELP,
    )
    group.addoption(
        "--cry17-nb-tests",
        action="store_true",
        dest="cry17_nb_tests",
        default=False,
        help=CRY17_NB_TEST_HELP,
    )
    group.addoption(
        "--cry17-nb-tests-only",
        action="store_true",
        dest="cry17_nb_tests_only",
        default=False,
        help=CRY17_NB_TEST_HELP,
    )

    parser.addini("cry17_no_mock", CRY17_NO_MOCK_HELP, type="bool", default=NotSet())
    parser.addini("cry17_workdir", CRY17_WORKDIR_HELP, default=NotSet())


def use_mock_exec(config):
    """Return whether mock executables should be used."""
    if config.getoption("cry17_no_mock"):
        return False
    ini = config.getini("cry17_no_mock")
    return True if isinstance(ini, NotSet) else not ini


def get_work_directory(config):
    """Return the aiida work directory to use."""
    if config.getoption("cry17_workdir") is not None:
        return config.getoption("cry17_workdir")
    ini = config.getini("cry17_workdir")
    if isinstance(ini, NotSet):
        return None
    return ini


def pytest_configure(config):
    # type: (Config) -> None
    """Register pytest markers.

    These will show in ``pytest --markers``
    """
    config.addinivalue_line(
        "markers",
        "{}: mark tests that will call external executables".format(
            CRY17_CALL_EXEC_MARKER
        ),
    )
    config.addinivalue_line(
        "markers",
        "{}: mark tests that will test document notebooks".format(
            CRY17_NOTEBOOK_MARKER
        ),
    )


def pytest_collection_modifyitems(config, items):
    # type: (Config, list) -> None
    """Modify collected test items (may filter or re-order the items in-place).

    If ``cry17_nb_tests_only == True``, deselect all tests not marked ``cry17_doc_notebooks``.

    Add skip marker to tests marked:

    - ``cry17_calls_executable`` if ``cry17_skip_exec == True``
    - ``cry17_calls_executable(skip_non_mock=True)`` if ``cry17_no_mock == True``.
    - ``cry17_doc_notebooks`` if ``cry17_nb_tests != True``

    """
    if config.getoption("cry17_nb_tests_only", False):
        # only run tests marked with CRY17_NOTEBOOK_MARKER
        items[:] = [item for item in items if CRY17_NOTEBOOK_MARKER in item.keywords]

    test_nbs = config.getoption("cry17_nb_tests", False) or config.getoption(
        "cry17_nb_tests_only", False
    )

    for item in items:  # type: Item

        if (not test_nbs) and (CRY17_NOTEBOOK_MARKER in item.keywords):
            item.add_marker(pytest.mark.skip(reason="cry17_nb_tests not specified"))
            continue

        if CRY17_CALL_EXEC_MARKER in item.keywords:

            marker = item.get_closest_marker(CRY17_CALL_EXEC_MARKER)

            if config.getoption("cry17_skip_exec", False):
                item.add_marker(pytest.mark.skip(reason="cry17_skip_exec specified"))
            elif marker.kwargs.get("skip_non_mock", False) and not use_mock_exec(
                config
            ):
                reason = marker.kwargs.get("reason", "")
                item.add_marker(
                    pytest.mark.skip(
                        reason="cry17_no_mock specified and skip_non_mock=True: {}".format(
                            reason
                        )
                    )
                )


def pytest_report_header(config):
    """Add header information for pytest execution."""
    if use_mock_exec(config):
        header = ["CRYSTAL17 Executables: mock_crystal17 mock_properties17"]
    else:
        header = ["CRYSTAL17 Executables: crystal17 properties17"]
    workdir = get_work_directory(config)
    workdir = workdir or "<TEMP>"
    header.append("CRYSTAL17 Work Directory: {}".format(workdir))
    return header


@pytest.fixture(scope="function")
def db_test_app(aiida_profile, pytestconfig):
    """Create a clean aiida database, profile and temporary work directory for the duration of a test.

    :rtype: aiida_crystal17.tests.utils.AiidaTestApp

    """
    if use_mock_exec(pytestconfig):
        print("NB: using mock executable")
        executables = {
            "crystal17.basic": "mock_crystal17",
            "crystal17.main": "mock_crystal17",
            "crystal17.doss": "mock_properties17",
            "crystal17.ech3": "mock_properties17",
            "crystal17.newk": "mock_properties17",
            "crystal17.ppan": "mock_properties17",
        }
    else:
        executables = {
            "crystal17.basic": "crystal17",
            "crystal17.main": "crystal17",
            "crystal17.doss": "properties17",
            "crystal17.ech3": "properties17",
            "crystal17.newk": "properties17",
            "crystal17.ppan": "properties17",
        }

    test_workdir = get_work_directory(pytestconfig)
    if test_workdir:
        print("NB: using test workdir: {}".format(test_workdir))
        work_directory = test_workdir
    else:
        work_directory = tempfile.mkdtemp()
    yield AiidaTestApp(work_directory, executables, environment=aiida_profile)
    aiida_profile.reset_db()
    if not test_workdir:
        shutil.rmtree(work_directory)


@pytest.fixture(scope="function")
def get_structure():
    """Return a function that returns a test `aiida.orm.StructureData` instance."""
    return get_test_structure


@pytest.fixture(scope="function")
def get_structure_and_symm():
    """Return a function that returns test `aiida.orm.StructureData` and `SymmetryData` instances."""
    return get_test_structure_and_symm


@pytest.fixture(scope="function")
def get_cif():
    """Return a function that returns a test `aiida.orm.CifData` instance."""  # noqa: D202

    def _get_cif(name):
        from aiida.orm import CifData

        if name == "pyrite":
            with open_resource_binary("cif", "pyrite.cif") as handle:
                return CifData(file=handle)
        raise ValueError(name)

    return _get_cif


@pytest.fixture(scope="function")
def upload_basis_set_family():
    """Upload a basis set family."""
    from aiida_crystal17.data.basis_set import BasisSetData

    def _upload(folder_name="sto3g", group_name="sto3g", stop_if_existing=True):
        with resource_context("basis_sets", folder_name) as path:
            BasisSetData.upload_basisset_family(
                path,
                group_name,
                "minimal basis sets",
                stop_if_existing=stop_if_existing,
                extension=".basis",
            )
        return BasisSetData.get_basis_group_map(group_name)

    return _upload


@pytest.fixture()
def sanitise_calc_attr():
    def _func(data: dict):
        return {
            k: v
            for k, v in data.items()
            if k
            not in [
                "job_id",
                "submit_script_filename",
                "scheduler_lastchecktime",
                "detailed_job_info",
                "last_job_info",
                "remote_workdir",
                "version",
            ]
        }

    return _func
