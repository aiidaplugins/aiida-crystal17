""" tests for the plugin

Use the aiida.utils.fixtures.PluginTestCase class for convenient
testing that does not pollute your profiles/databases.
"""
# Helper functions for tests
import inspect
import os
import stat
import subprocess
import sys

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_COMPUTER = 'localhost-test'

executables = {
    'crystal17.diff': 'diff',
    'crystal17.basic': 'runcry17',
    'crystal17.main': 'runcry17',
}

MOCK_GLOBAL_VAR = "MOCK_EXECUTABLES"

mock_executables = {
    'crystal17.diff': 'diff',
    'crystal17.basic': 'mock_runcry17',
    'crystal17.main': 'mock_runcry17',
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
    path = None

    # issue with distutils finding scripts within the python path (i.e. those created by pip install)
    script_path = os.path.join(os.path.dirname(sys.executable), executable)
    if os.path.exists(script_path):
        path = script_path

    if path is None:
        # pylint issue https://github.com/PyCQA/pylint/issues/73
        import distutils.spawn  # pylint: disable=no-name-in-module,import-error
        path = distutils.spawn.find_executable(executable)

    if path is None:
        raise ValueError("{} executable not found in PATH.".format(executable))

    return os.path.abspath(path)


def get_computer(name=TEST_COMPUTER, workdir=None, configure=False):
    """Get local computer.

    Sets up local computer with 'name' or reads it from database,
    if it exists.
    
    :param name: Name of local computer
    :param workdir: path to work directory (required if creating a new computer)
    :param configure: whether to congfigure a new computer for the user email

    :return: The computer node 
    :rtype: :py:class:`aiida.orm.Computer` 
    """
    from aiida.orm import Computer
    from aiida.common.exceptions import NotExistent

    try:
        computer = Computer.get(name)
    except NotExistent:

        if workdir is None:
            raise ValueError(
                "to create a new computer, a work directory must be supplied")

        computer = Computer(
            name=name,
            description='localhost computer set up by aiida_crystal17 tests',
            hostname=name,
            workdir=workdir,
            transport_type='local',
            scheduler_type='direct',
            enabled_state=True)
        computer.store()

        if configure:
            try:
                # aiida-core v1
                from aiida.control.computer import configure_computer
                configure_computer(computer)
            except ImportError:
                configure_computer_v012(computer)

    return computer


def configure_computer_v012(computer, user_email=None, authparams=None):
    """Configure the authentication information for a given computer

    adapted from aiida-core v0.12.2:
    aiida_core.aiida.cmdline.commands.computer.Computer.computer_configure

    :param computer: the computer to authenticate against
    :param user_email: the user email (otherwise use default)
    :param authparams: a dictionary of additional authorisation parameters to use (in string format)
    :return:
    """
    from aiida.common.exceptions import ValidationError
    from aiida.backends.utils import get_automatic_user
    # aiida-core v1
    # from aiida.orm.backend import construct_backend
    # backend = construct_backend()
    # get_automatic_user = backend.users.get_automatic_user

    authparams = {} if authparams is None else authparams
    transport = computer.get_transport_class()
    valid_keys = transport.get_valid_auth_params()

    if user_email is None:
        user = get_automatic_user()
    else:
        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        qb.append(type="user", filters={'email': user_email})
        user = qb.first()
        if not user:
            raise ValueError("user email not found: {}".format(user_email))
        user = user[0]._dbuser  # for Django, the wrong user class is returned

    authinfo, old_authparams = _get_auth_info(computer, user)

    # print ("Configuring computer '{}' for the AiiDA user '{}'".format(
    #     computername, user.email))
    #
    # print "Computer {} has transport of type {}".format(computername,
    #                                                     computer.get_transport_type())

    # from aiida.common.utils import get_configured_user_email
    # if user.email != get_configured_user_email():
    # print "*" * 72
    # print "** {:66s} **".format("WARNING!")
    # print "** {:66s} **".format(
    #     "  You are configuring a different user.")
    # print "** {:66s} **".format(
    #     "  Note that the default suggestions are taken from your")
    # print "** {:66s} **".format(
    #     "  local configuration files, so they may be incorrect.")
    # print "*" * 72

    default_authparams = {}
    for k in valid_keys:
        if k in old_authparams:
            default_authparams[k] = old_authparams.pop(k)
            if k not in authparams:
                authparams[k] = default_authparams[k]

    if old_authparams:
        print("WARNING: the following keys were previously in the "
              "authorization parameters, but have not been recognized "
              "and have been deleted: {}".format(", ".join(
                  old_authparams.keys())))

    if set(authparams.keys()) != set(valid_keys):
        raise ValueError(
            "new_authparams should contain only the keys: {}".format(
                valid_keys))

    # convert keys from strings
    transport_members = dict(inspect.getmembers(transport))
    for k, txtval in authparams.items():

        converter_name = '_convert_{}_fromstring'.format(k)
        suggester_name = '_get_{}_suggestion_string'.format(k)
        if converter_name not in transport_members:
            raise ValueError("No {} defined in Transport {}".format(
                converter_name, computer.get_transport_type()))
        converter = transport_members[converter_name]

        suggestion = ""
        if k in default_authparams:
            suggestion = default_authparams[k]
        elif suggester_name in transport_members:
            suggestion = transport_members[suggester_name](computer)

        try:
            authparams[k] = converter(txtval)
        except ValidationError, err:
            raise ValueError("error in the authparam "
                             "{0}: {1}, suggested value: {2}".format(
                                 k, err, suggestion))

    authinfo.set_auth_params(authparams)
    authinfo.save()


def _get_auth_info(computer, user):
    from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
    from django.core.exceptions import ObjectDoesNotExist

    BACKEND = get_backend()
    if BACKEND == BACKEND_DJANGO:
        from aiida.backends.djsite.db.models import DbAuthInfo

        try:
            authinfo = DbAuthInfo.objects.get(
                dbcomputer=computer.dbcomputer, aiidauser=user)

            old_authparams = authinfo.get_auth_params()
        except ObjectDoesNotExist:
            authinfo = DbAuthInfo(
                dbcomputer=computer.dbcomputer, aiidauser=user)
            old_authparams = {}

    elif BACKEND == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
        from aiida.backends.sqlalchemy import get_scoped_session

        session = get_scoped_session()
        # TODO sqlalchemy get_scoped_session returns None
        authinfo = session.query(DbAuthInfo).filter(
            DbAuthInfo.dbcomputer == computer.dbcomputer).filter(
                DbAuthInfo.aiidauser == user).first()

        if authinfo is None:
            authinfo = DbAuthInfo(
                dbcomputer=computer.dbcomputer, aiidauser=user)
            old_authparams = {}
        else:
            old_authparams = authinfo.get_auth_params()
    else:
        raise Exception("Unknown backend {}".format(BACKEND))

    return authinfo, old_authparams


def get_code(entry_point, computer):
    """Get local code.

    Sets up code for given entry point on given computer.
    
    :param entry_point: Entry point of calculation plugin
    :param computer: computer

    :return: The code node 
    :rtype: :py:class:`aiida.orm.Code` 
    """
    from aiida.orm import Code
    from aiida.common.exceptions import NotExistent

    if os.environ.get(MOCK_GLOBAL_VAR, False):
        print("NB: using mock executable")
        exec_lookup = mock_executables
    else:
        exec_lookup = executables

    try:
        executable = exec_lookup[entry_point]
    except KeyError:
        raise KeyError("Entry point {} not recognized. Allowed values: {}"
                       .format(entry_point, exec_lookup.keys()))

    try:
        code = Code.get_from_string('{}-{}@{}'.format(entry_point, executable,
                                                      computer.get_name()))
    except NotExistent:
        path = get_path_to_executable(executable)
        code = Code(
            input_plugin_name=entry_point,
            remote_computer_exec=[computer, path],
        )
        code.label = '{}-{}'.format(entry_point, executable)
        code.store()

    return code


def test_calculation_execution(calc,
                               allowed_returncodes=(0, ),
                               check_paths=None):
    """ test that a calculation executes successfully

    :param calc: the calculation
    :param allowed_returncodes: raise RunTimeError if return code is not in allowed_returncodes
    :param check_paths: raise OSError if these relative paths are not in the folder after execution
    :return:
    """
    from aiida.common.folders import SandboxFolder

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:

        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created at {}".format(subfolder.abspath))

        script_path = os.path.join(subfolder.abspath, script_filename)
        scheduler_stderr = calc._SCHED_ERROR_FILE

        # we first need to make sure the script is executable
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
        # now call script, NB: bash -l -c is required to access global variable loaded in .bash_profile
        returncode = subprocess.call(
            ["bash", "-l", "-c", script_path], cwd=subfolder.abspath)

        if returncode not in allowed_returncodes:

            err_msg = "process failed (and couldn't find stderr file: {})".format(
                scheduler_stderr)
            stderr_path = os.path.join(subfolder.abspath, scheduler_stderr)
            if os.path.exists(stderr_path):
                with open(stderr_path) as f:
                    err_msg = "Process failed with stderr:\n{}".format(
                        f.read())
            raise RuntimeError(err_msg)

        if check_paths is not None:
            for outpath in check_paths:
                subfolder.get_abs_path(outpath, check_existence=True)

        print("calculation completed execution")
