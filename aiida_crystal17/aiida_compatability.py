"""Utilities for working with different versions of aiida"""
from packaging import version
from functools import wraps
import json
import datetime


def aiida_version():
    """get the version of aiida in use

    :returns: packaging.version.Version
    """
    from aiida import __version__ as aiida_version_
    return version.parse(aiida_version_)


def cmp_version(string):
    """convert a version string to a packaging.version.Version"""
    return version.parse(string)


def cmp_load_verdi_data():
    """Load the verdi data click command group for any version since 0.11."""
    verdi_data = None
    import_errors = []

    try:
        from aiida.cmdline.commands import data_cmd as verdi_data
    except ImportError as err:
        import_errors.append(err)

    if not verdi_data:
        try:
            from aiida.cmdline.commands import verdi_data
        except ImportError as err:
            import_errors.append(err)

    if not verdi_data:
        try:
            from aiida.cmdline.commands.cmd_data import verdi_data
        except ImportError as err:
            import_errors.append(err)

    if not verdi_data:
        err_messages = '\n'.join(
            [' * {}'.format(error) for error in import_errors])
        raise ImportError(
            'The verdi data base command group could not be found:\n' +
            err_messages)

    return verdi_data


def run_get_node(process, inputs_dict):
    """ an implementation of run_get_node which is compatible with both aiida v0.12 and v1.0.0

    it will also convert "options" "label" and "description" to/from the _ variant

    :param process: a process
    :param inputs_dict: a dictionary of inputs
    :type inputs_dict: dict
    :return: the calculation Node
    """
    if aiida_version() < cmp_version("1.0.0a1"):
        for key in ["options", "label", "description"]:
            if key in inputs_dict:
                inputs_dict["_" + key] = inputs_dict.pop(key)
        workchain = process.new_instance(inputs=inputs_dict)
        workchain.run_until_complete()
        calcnode = workchain.calc
    else:
        from aiida.work.launch import run_get_node  # pylint: disable=import-error
        for key in ["_options", "_label", "_description"]:
            if key in inputs_dict:
                inputs_dict[key[1:]] = inputs_dict.pop(key)
        _, calcnode = run_get_node(process, **inputs_dict)

    return calcnode


def load_dbenv_if_not_loaded(**kwargs):
    """Load dbenv if necessary, run spinner meanwhile to show command hasn't crashed."""
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv(**kwargs)


def dbenv(function):
    """A function decorator that loads the dbenv if necessary before running the function."""

    @wraps(function)
    def decorated_function(*args, **kwargs):
        """Load dbenv if not yet loaded, then run the original function."""
        load_dbenv_if_not_loaded()
        return function(*args, **kwargs)

    return decorated_function


def get_data_node(data_type, *args, **kwargs):
    return get_data_class(data_type)(*args, **kwargs)


@dbenv
def get_data_class(data_type):
    """
    Provide access to the orm.data classes with deferred dbenv loading.

    compatiblity: also provide access to the orm.data.base memebers, which are loadable through the DataFactory as of 1.0.0-alpha only.
    """
    from aiida.orm import DataFactory
    from aiida.common.exceptions import MissingPluginError
    data_cls = None
    try:
        data_cls = DataFactory(data_type)
    except MissingPluginError as err:
        if data_type in BASIC_DATA_TYPES:
            data_cls = get_basic_data_pre_1_0(data_type)
        else:
            raise err
    return data_cls


BASIC_DATA_TYPES = set(['bool', 'float', 'int', 'list', 'str'])


@dbenv
def get_basic_data_pre_1_0(data_type):
    from aiida.orm.data import base as base_data
    return getattr(base_data, data_type.capitalize())


@dbenv
def get_automatic_user():
    try:
        from aiida.backends.utils import get_automatic_user
        automatic_user = get_automatic_user()
    except ImportError:
        from aiida.orm.backend import construct_backend
        backend = construct_backend()
        automatic_user = backend.users.get_automatic_user()
    return automatic_user


def json_default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return None


def get_calc_log(calcnode):
    """get a formatted string of the calculation log"""
    from aiida.backends.utils import get_log_messages

    log_string = "- Calc State:\n{0}\n- Scheduler Out:\n{1}\n- Scheduler Err:\n{2}\n- Log:\n{3}".format(
        calcnode.get_state(), calcnode.get_scheduler_output(),
        calcnode.get_scheduler_error(),
        json.dumps(get_log_messages(calcnode), default=json_default, indent=2))
    return log_string


# @dbenv
# def backend_obj_users():
#     """Test if aiida accesses users through backend object."""
#     backend_obj_flag = False
#     try:
#         from aiida.backends.utils import get_automatic_user  # pylint: disable=unused-variable,no-name-in-module
#     except ImportError:
#         backend_obj_flag = True
#     return backend_obj_flag
