"""
initialise a text database and profile
"""
from contextlib import contextmanager
import distutils.spawn
import os
import shutil
import sys
import tempfile

from aiida.manage.fixtures import fixture_manager
import pytest

executables = {
    'crystal17.basic': 'runcry17',
    'crystal17.main': 'runcry17',
}
MOCK_GLOBAL_VAR = "MOCK_CRY17_EXECUTABLES"
mock_executables = {
    'crystal17.basic': 'mock_runcry17',
    'crystal17.main': 'mock_runcry17',
}


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
    yield AiidaTestApp(aiida_profile, work_directory)
    aiida_profile.reset_db()
    shutil.rmtree(work_directory)


class AiidaTestApp(object):
    def __init__(self, profile, work_directory):
        self._profile = profile
        self._work_directory = work_directory

    @property
    def work_directory(self):
        return self._work_directory

    @property
    def profile(self):
        return self._profile

    @staticmethod
    def get_backend():
        from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
        if os.environ.get('TEST_AIIDA_BACKEND') == BACKEND_SQLA:
            return BACKEND_SQLA
        return BACKEND_DJANGO

    @staticmethod
    def get_path_to_executable(executable):
        """ Get path to local executable.

        :param executable: Name of executable in the $PATH variable
        :type executable: str

        :return: path to executable
        :rtype: str
        """
        path = None

        # issue with distutils finding scripts within the python path
        # (i.e. those created by pip install)
        script_path = os.path.join(os.path.dirname(sys.executable), executable)
        if os.path.exists(script_path):
            path = script_path
        if path is None:
            path = distutils.spawn.find_executable(executable)
        if path is None:
            raise ValueError(
                "{} executable not found in PATH.".format(executable))

        return os.path.abspath(path)

    def get_or_create_computer(self, name='localhost'):
        """Setup localhost computer"""
        from aiida.orm import Computer
        from aiida.common import NotExistent

        try:
            computer = Computer.objects.get(name=name)
        except NotExistent:

            computer = Computer(
                name=name,
                description=('localhost computer, '
                             'set up by aiida_crystal17 tests'),
                hostname='localhost',
                workdir=self.work_directory,
                transport_type='local',
                scheduler_type='direct',
                enabled_state=True)
            computer.store()
            computer.configure()

        return computer

    def get_or_create_code(self, entry_point, computer_name='localhost'):
        """Setup code on localhost computer"""
        from aiida.orm import Code
        from aiida.common import NotExistent

        computer = self.get_or_create_computer(computer_name)

        if os.environ.get(MOCK_GLOBAL_VAR, False):
            print("NB: using mock executable")
            exec_lookup = mock_executables
        else:
            exec_lookup = executables

        try:
            executable = exec_lookup[entry_point]
        except KeyError:
            raise KeyError(
                "Entry point {} not recognized. Allowed values: {}".format(
                    entry_point, exec_lookup.keys()))

        try:
            code = Code.objects.get(
                label='{}-{}@{}'.format(entry_point, executable,
                                        computer_name))
        except NotExistent:
            path = self.get_path_to_executable(executable)
            code = Code(
                input_plugin_name=entry_point,
                remote_computer_exec=[computer, path],
            )
            code.label = '{}-{}@{}'.format(
                entry_point, executable, computer_name)
            code.store()

        return code

    @contextmanager
    def with_folder(self):
        """AiiDA folder object context.

        Useful for calculation.submit_test()
        """
        from aiida.common.folders import Folder
        temp_dir = tempfile.mkdtemp()
        try:
            yield Folder(temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    @staticmethod
    def check_calculation(
            calc_node, expected_outgoing_labels,
            error_include=(("results", "errors"),
                           ("results", "parser_errors"))):
        """ check a calculation has completed successfully """

        exit_status = calc_node.get_attribute("exit_status")
        proc_state = calc_node.get_attribute("process_state")
        if exit_status != 0 or proc_state != "finished":
            message = (
                "Process Failed: "
                "exit status: {0}\nprocess state: {1}\ncalc attributes: {2}").format(
                exit_status, proc_state, calc_node.attributes)
            out_link_manager = calc_node.get_outgoing()
            out_links = out_link_manager.all_link_labels()
            message += "\noutgoing_nodes: {}".format(out_links)
            for name, attribute in error_include:
                if name not in out_links:
                    continue
                value = out_link_manager.get_node_by_label(name).get_attribute(attribute, None)
                if value is None:
                    continue
                message += "\n{}.{}: {}".format(name, attribute, value)
            raise AssertionError(message)

        link_labels = calc_node.get_outgoing().all_link_labels()
        for outgoing in expected_outgoing_labels:
            if outgoing not in link_labels:
                raise AssertionError(
                    "missing outgoing node link '{}': {}".format(
                        outgoing, link_labels))
