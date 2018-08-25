""" tests for the plugin

Use the aiida.utils.fixtures.PluginTestCase class for convenient
testing that does not pollute your profiles/databases.
"""
# Helper functions for tests
import os
import tempfile
import stat
import subprocess
import sys

TEST_DIR = os.path.dirname(os.path.realpath(__file__))

executables = {
    'diff': 'diff',
    'crystal17.basic': 'runcry17',
}

MOCK_GLOBAL_VAR = "MOCK_EXECUTABLES"

mock_executables = {
    'diff': 'diff',
    'crystal17.basic': 'mock_runcry17',
}


def get_backend():
    """ Return database backend.

    Reads from 'TEST_AIIDA_BACKEND' environment variable.
    Defaults to django backend.
    """
    from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
    if os.environ.get('TEST_AIIDA_BACKEND') == BACKEND_SQLA:
        return BACKEND_SQLA
    return BACKEND_DJANGO


def get_path_to_executable(executable):
    """ Get path to local executable.

    :param executable: Name of executable in the $PATH variable
    :type executable: str

    :return: path to executable
    :rtype: str
    """
    # pylint issue https://github.com/PyCQA/pylint/issues/73
    import distutils.spawn  # pylint: disable=no-name-in-module,import-error
    path = distutils.spawn.find_executable(executable)
    if path is None:
        # distutils cannot find scripts within the python path (i.e. those created by pip install)
        script_path = os.path.join(os.path.dirname(sys.executable), executable)
        if os.path.exists(script_path):
            path = script_path

    if path is None:
        raise ValueError("{} executable not found in PATH.".format(executable))

    return path


def get_computer(name='localhost'):
    """Get local computer.

    Sets up local computer with 'name' or reads it from database,
    if it exists.
    
    :param name: Name of local computer

    :return: The computer node 
    :rtype: :py:class:`aiida.orm.Computer` 
    """
    from aiida.orm import Computer
    from aiida.common.exceptions import NotExistent

    try:
        computer = Computer.get(name)
    except NotExistent:

        computer = Computer(
            name=name,
            description='localhost computer set up by aiida_crystal17 tests',
            hostname='localhost',
            workdir=tempfile.mkdtemp(),
            transport_type='local',
            scheduler_type='direct',
            enabled_state=True)
        computer.store()

    return computer


def get_code(entry_point, computer_name='localhost'):
    """Get local code.

    Sets up code for given entry point on given computer.
    
    :param entry_point: Entry point of calculation plugin
    :param computer_name: Name of (local) computer

    :return: The code node 
    :rtype: :py:class:`aiida.orm.Code` 
    """
    from aiida.orm import Code
    from aiida.common.exceptions import NotExistent

    computer = get_computer(computer_name)

    if os.environ.get(MOCK_GLOBAL_VAR, False):
        exec_lookup = mock_executables
    else:
        exec_lookup = executables

    try:
        executable = exec_lookup[entry_point]
    except KeyError:
        raise KeyError("Entry point {} not recognized. Allowed values: {}"
                       .format(entry_point, exec_lookup.keys()))

    try:
        code = Code.get_from_string('{}@{}'.format(executable, computer_name))
    except NotExistent:
        path = get_path_to_executable(executable)
        code = Code(
            input_plugin_name=entry_point,
            remote_computer_exec=[computer, path],
        )
        code.label = executable
        code.store()

    return code


def test_calculation_execution(calc, allowed_returncodes=(0,)):
    """test that a calculation executes successfully"""
    from aiida.common.folders import SandboxFolder

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:

        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created at {}".format(subfolder.abspath))

        script_path = os.path.join(subfolder.abspath, script_filename)
        # we first need to make sure the script is executable
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
        # now call script, NB: bash -l -c is required to access global variable loaded in .bash_profile

        returncode = subprocess.call(["bash", "-l", "-c", script_path], cwd=subfolder.abspath)

        if returncode not in allowed_returncodes:
            # the script reroutes stderr to _scheduler-stderr.txt (at least in v0.12)
            err_msg = "process failed (and couldn't find _scheduler-stderr.txt)"
            stderr_path = os.path.join(subfolder.abspath, "_scheduler-stderr.txt")
            if os.path.exists(stderr_path):
                with open(stderr_path) as f:
                    err_msg = "Process failed with stderr:\n{}".format(f.read())
            raise RuntimeError(err_msg)
        print("calculation completed execution")
